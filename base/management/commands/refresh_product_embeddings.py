from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from base.embeddings import build_product_embedding_text, get_embedding_provider, get_product_content_hash
from base.models import Product, ProductEmbedding


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


class Command(BaseCommand):
    help = 'Generate or refresh product embeddings using the configured embedding provider.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Regenerate embeddings even if the product text is unchanged.')
        parser.add_argument(
            '--batch-size',
            type=int,
            default=int(getattr(settings, 'RECOMMENDATION_EMBEDDING_BATCH_SIZE', 32)),
            help='Number of products to send in each embedding request.',
        )
        parser.add_argument(
            '--product-id',
            type=int,
            action='append',
            dest='product_ids',
            help='Limit embedding refresh to specific product ids.',
        )

    def handle(self, *args, **options):
        try:
            provider = get_embedding_provider()
        except ImproperlyConfigured as exc:
            raise CommandError(str(exc)) from exc

        products = Product.objects.filter(is_active=True).select_related('tenant', 'category').order_by('id')
        product_ids = options.get('product_ids') or []
        if product_ids:
            products = products.filter(id__in=product_ids)

        product_list = list(products)
        if not product_list:
            self.stdout.write(self.style.WARNING('No active products found for embedding generation.'))
            return

        existing_embeddings = {
            embedding.product_id: embedding
            for embedding in ProductEmbedding.objects.filter(product_id__in=[product.id for product in product_list])
        }

        updated_count = 0
        skipped_count = 0
        batch_size = max(1, options['batch_size'])

        for batch in chunked(product_list, batch_size):
            pending_products = []
            batch_texts = []

            for product in batch:
                content_hash = get_product_content_hash(product)
                existing = existing_embeddings.get(product.id)
                if existing and existing.content_hash == content_hash and not options['force']:
                    skipped_count += 1
                    continue

                pending_products.append((product, content_hash))
                batch_texts.append(build_product_embedding_text(product))

            if not pending_products:
                continue

            vectors = provider.embed_texts(batch_texts)
            for (product, content_hash), vector in zip(pending_products, vectors):
                ProductEmbedding.objects.update_or_create(
                    product=product,
                    defaults={
                        'model_name': provider.model_name,
                        'content_hash': content_hash,
                        'vector': vector,
                    },
                )
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Embeddings refreshed. Updated: {updated_count}, skipped: {skipped_count}, provider: {provider.model_name}.'
            )
        )