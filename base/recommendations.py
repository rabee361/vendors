from django.conf import settings
from django.db.models import Case, Count, IntegerField, Min, Q, Sum, Value, When

from .models import (
    CartItem,
    Favorite,
    OrderItem,
    Product,
    ProductRating,
    ProductRecommendation,
    SponsoredAdClick,
    UserRecommendation,
)


def _base_products_queryset():
    return (
        Product.objects.select_related('tenant', 'category', 'tenant__category')
        .prefetch_related('ratings')
        .filter(is_active=True)
    )


def _ordered_products(product_ids):
    if not product_ids:
        return []

    products = _base_products_queryset().filter(id__in=product_ids)
    products_by_id = {product.pk: product for product in products}
    return [products_by_id[product_id] for product_id in product_ids if product_id in products_by_id]


def _get_user_seen_product_ids(user):
    if not user.is_authenticated:
        return set()

    seen_ids = set(
        OrderItem.objects.filter(order__email=user.email, product__isnull=False).values_list('product_id', flat=True)
    )
    seen_ids.update(Favorite.objects.filter(user=user).values_list('product_id', flat=True))
    seen_ids.update(ProductRating.objects.filter(user=user).values_list('product_id', flat=True))
    seen_ids.update(CartItem.objects.filter(cart__user=user).values_list('product_id', flat=True))
    seen_ids.update(
        SponsoredAdClick.objects.filter(user=user, ad__product__isnull=False).values_list('ad__product_id', flat=True)
    )
    return {product_id for product_id in seen_ids if product_id}


def get_fallback_products(limit, exclude_ids=None, preferred_category_id=None, preferred_vendor_ids=None):
    exclude_ids = [product_id for product_id in (exclude_ids or []) if product_id]
    preferred_vendor_ids = [vendor_id for vendor_id in (preferred_vendor_ids or []) if vendor_id]

    products = _base_products_queryset()
    if exclude_ids:
        products = products.exclude(id__in=exclude_ids)

    products = products.annotate(
        category_match=Case(
            When(category_id=preferred_category_id, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        vendor_match=Case(
            When(tenant_id__in=preferred_vendor_ids, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        popularity=Count('orderitem', distinct=True)
        + Count('favorited_by', distinct=True)
        + Count('ratings', distinct=True),
    ).order_by('-category_match', '-vendor_match', '-popularity', '-created_at')

    return list(products[:limit])


def get_related_products(product, limit=None):
    if limit is None:
        limit = int(getattr(settings, 'RECOMMENDATION_PRODUCT_LIMIT', 6))

    recommended_ids = list(
        ProductRecommendation.objects.filter(source_product=product)
        .order_by('rank', '-score')
        .values_list('recommended_product_id', flat=True)[:limit]
    )
    if recommended_ids:
        return _ordered_products(recommended_ids)

    return get_fallback_products(
        limit=limit,
        exclude_ids=[product.id],
        preferred_category_id=product.category_id,
        preferred_vendor_ids=[product.tenant_id],
    )


def get_user_recommendations(user, limit=None, exclude_ids=None):
    if limit is None:
        limit = int(getattr(settings, 'RECOMMENDATION_PRODUCT_LIMIT', 6))

    exclude_ids = set(exclude_ids or [])
    if not user.is_authenticated:
        return get_fallback_products(limit=limit, exclude_ids=exclude_ids)

    recommended_ids = list(
        UserRecommendation.objects.filter(user=user)
        .exclude(product_id__in=exclude_ids)
        .order_by('rank', '-score')
        .values_list('product_id', flat=True)[:limit]
    )
    if recommended_ids:
        return _ordered_products(recommended_ids)

    seen_ids = _get_user_seen_product_ids(user)
    preferred_vendor_ids = list(
        Product.objects.filter(id__in=seen_ids).values_list('tenant_id', flat=True).distinct()[:3]
    )
    preferred_category_id = (
        Product.objects.filter(id__in=seen_ids).values_list('category_id', flat=True).exclude(category_id__isnull=True).first()
    )

    return get_fallback_products(
        limit=limit,
        exclude_ids=seen_ids.union(exclude_ids),
        preferred_category_id=preferred_category_id,
        preferred_vendor_ids=preferred_vendor_ids,
    )


def get_cart_recommendations(user, cart_product_ids, limit=None):
    if limit is None:
        limit = int(getattr(settings, 'RECOMMENDATION_CART_LIMIT', 2))

    normalized_ids = []
    for product_id in cart_product_ids:
        try:
            normalized_ids.append(int(product_id))
        except (TypeError, ValueError):
            continue

    if normalized_ids:
        aggregated_ids = list(
            ProductRecommendation.objects.filter(source_product_id__in=normalized_ids)
            .exclude(recommended_product_id__in=normalized_ids)
            .values('recommended_product_id')
            .annotate(total_score=Sum('score'), best_rank=Min('rank'))
            .order_by('-total_score', 'best_rank', 'recommended_product_id')[:limit]
        )
        product_ids = [row['recommended_product_id'] for row in aggregated_ids]
        if product_ids:
            return _ordered_products(product_ids)

    return get_user_recommendations(user, limit=limit, exclude_ids=normalized_ids)