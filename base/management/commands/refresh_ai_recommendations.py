import math
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from base.models import (
    CartItem,
    Favorite,
    OrderItem,
    ProductEmbedding,
    ProductRecommendation,
    ProductRating,
    SponsoredAdClick,
    UserRecommendation,
)
from utils.types import UserType


def cosine_similarity(left_vector, right_vector):
    if not left_vector or not right_vector or len(left_vector) != len(right_vector):
        return 0.0

    numerator = sum(float(left) * float(right) for left, right in zip(left_vector, right_vector))
    left_norm = math.sqrt(sum(float(value) * float(value) for value in left_vector))
    right_norm = math.sqrt(sum(float(value) * float(value) for value in right_vector))

    if not left_norm or not right_norm:
        return 0.0

    return numerator / (left_norm * right_norm)


class Command(BaseCommand):
    help = 'Refresh cached product and user recommendations using stored embeddings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-limit',
            type=int,
            default=int(getattr(settings, 'RECOMMENDATION_PRODUCT_LIMIT', 6)),
            help='Number of related products to store per product.',
        )
        parser.add_argument(
            '--user-limit',
            type=int,
            default=int(getattr(settings, 'RECOMMENDATION_USER_LIMIT', 12)),
            help='Number of recommended products to store per user.',
        )

    def handle(self, *args, **options):
        product_limit = max(1, options['product_limit'])
        user_limit = max(1, options['user_limit'])

        with transaction.atomic():
            product_count = self._refresh_product_recommendations(product_limit)
            user_count = self._refresh_user_recommendations(user_limit)

        self.stdout.write(
            self.style.SUCCESS(
                f'Recommendations refreshed. Product rows: {product_count}, user rows: {user_count}.'
            )
        )

    def _refresh_product_recommendations(self, limit):
        embeddings = list(
            ProductEmbedding.objects.select_related('product', 'product__tenant', 'product__category')
            .filter(product__is_active=True)
            .order_by('product_id')
        )
        if not embeddings:
            ProductRecommendation.objects.filter(source=ProductRecommendation.SOURCE_HYBRID).delete()
            return 0

        recommendation_rows = []
        ProductRecommendation.objects.filter(source=ProductRecommendation.SOURCE_HYBRID).delete()

        for embedding in embeddings:
            embedding_scores = self._get_embedding_neighbor_scores(embedding, limit * 4)
            copurchase_scores = self._get_copurchase_scores(embedding.product_id)
            candidate_ids = set(embedding_scores.keys()) | set(copurchase_scores.keys())

            ranked_candidates = []
            for candidate_id in candidate_ids:
                scores = []
                reason_bits = []

                embedding_score = embedding_scores.get(candidate_id)
                if embedding_score:
                    scores.append((0.45, embedding_score))
                    reason_bits.append('embedding')

                copurchase_score = copurchase_scores.get(candidate_id)
                if copurchase_score:
                    scores.append((0.55, copurchase_score))
                    reason_bits.append('co-purchase')

                if not scores:
                    continue

                total_weight = sum(weight for weight, _ in scores)
                final_score = sum(weight * score for weight, score in scores) / total_weight
                ranked_candidates.append((candidate_id, final_score, '+'.join(reason_bits)))

            ranked_candidates.sort(key=lambda item: (-item[1], item[0]))

            for rank, (candidate_id, score, reason) in enumerate(ranked_candidates[:limit], start=1):
                recommendation_rows.append(
                    ProductRecommendation(
                        source_product_id=embedding.product_id,
                        recommended_product_id=candidate_id,
                        source=ProductRecommendation.SOURCE_HYBRID,
                        rank=rank,
                        score=score,
                        reason=reason,
                    )
                )

        ProductRecommendation.objects.bulk_create(recommendation_rows, batch_size=500)
        return len(recommendation_rows)

    def _refresh_user_recommendations(self, limit):
        user_model = get_user_model()
        users = user_model.objects.filter(is_active=True, user_type=UserType.BUYER).order_by('id')

        UserRecommendation.objects.filter(source=UserRecommendation.SOURCE_HYBRID).delete()
        recommendation_rows = []

        for user in users:
            product_weights = self._get_user_product_weights(user)
            if not product_weights:
                continue

            user_vector = self._build_user_vector(product_weights)
            if not user_vector:
                continue

            seen_product_ids = set(product_weights.keys())
            candidates = self._get_nearest_products(user_vector, seen_product_ids, limit)
            for rank, (product_id, score) in enumerate(candidates, start=1):
                recommendation_rows.append(
                    UserRecommendation(
                        user=user,
                        product_id=product_id,
                        source=UserRecommendation.SOURCE_HYBRID,
                        rank=rank,
                        score=score,
                        reason='user-embedding-profile',
                    )
                )

        UserRecommendation.objects.bulk_create(recommendation_rows, batch_size=500)
        return len(recommendation_rows)

    def _get_embedding_neighbor_scores(self, embedding, limit):
        scores = []
        for candidate in ProductEmbedding.objects.filter(product__is_active=True).exclude(product_id=embedding.product_id):
            score = cosine_similarity(embedding.vector, candidate.vector)
            if score > 0:
                scores.append((candidate.product_id, score))

        scores.sort(key=lambda item: (-item[1], item[0]))
        return dict(scores[:limit])

    def _get_copurchase_scores(self, product_id):
        related_order_ids = OrderItem.objects.filter(product_id=product_id).values_list('order_id', flat=True)
        co_purchases = list(
            OrderItem.objects.filter(order_id__in=related_order_ids, product__isnull=False)
            .exclude(product_id=product_id)
            .values('product_id')
            .annotate(total=Count('id'))
            .order_by('-total', 'product_id')
        )
        if not co_purchases:
            return {}

        max_total = max(row['total'] for row in co_purchases) or 1
        return {row['product_id']: row['total'] / max_total for row in co_purchases}

    def _get_user_product_weights(self, user):
        weights = defaultdict(float)

        for product_id in OrderItem.objects.filter(order__email=user.email, product__isnull=False).values_list('product_id', flat=True):
            weights[product_id] += 5.0

        for product_id in Favorite.objects.filter(user=user).values_list('product_id', flat=True):
            weights[product_id] += 3.0

        for product_id, rating in ProductRating.objects.filter(user=user).values_list('product_id', 'rating'):
            weights[product_id] += 1.5 + float(rating)

        for product_id, quantity in CartItem.objects.filter(cart__user=user).values_list('product_id', 'quantity'):
            weights[product_id] += min(quantity, 3) * 1.5

        for product_id in SponsoredAdClick.objects.filter(user=user, ad__product__isnull=False).values_list('ad__product_id', flat=True):
            weights[product_id] += 1.0

        return {product_id: weight for product_id, weight in weights.items() if weight > 0}

    def _build_user_vector(self, product_weights):
        embeddings = ProductEmbedding.objects.filter(product_id__in=product_weights.keys())
        embedding_list = list(embeddings)
        if not embedding_list:
            return None

        total_weight = 0.0
        weighted_vector = None

        for embedding in embedding_list:
            weight = product_weights.get(embedding.product_id, 0.0)
            if weight <= 0:
                continue

            if weighted_vector is None:
                weighted_vector = [0.0] * len(embedding.vector)

            for index, value in enumerate(embedding.vector):
                weighted_vector[index] += float(value) * weight
            total_weight += weight

        if not weighted_vector or total_weight <= 0:
            return None

        return [value / total_weight for value in weighted_vector]

    def _get_nearest_products(self, query_vector, exclude_product_ids, limit):
        scores = []
        for candidate in ProductEmbedding.objects.filter(product__is_active=True).exclude(product_id__in=exclude_product_ids):
            score = cosine_similarity(query_vector, candidate.vector)
            if score > 0:
                scores.append((candidate.product_id, score))

        scores.sort(key=lambda item: (-item[1], item[0]))
        return scores[:limit]