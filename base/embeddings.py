import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from sentence_transformers import SentenceTransformer


def build_product_embedding_text(product):
    parts = [f"passage: Product: {product.name}"]

    if product.category_id and product.category:
        parts.append(f"Category: {product.category.name}")

    if product.tenant_id and product.tenant:
        parts.append(f"Store: {product.tenant.store_name}")

    if product.description:
        parts.append(f"Description: {product.description.strip()}")

    parts.append(f"Price: {product.price}")
    parts.append(f"In stock: {product.stock}")

    return "\n".join(parts)


def get_product_content_hash(product):
    content = build_product_embedding_text(product)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

class SentenceTransformerEmbeddingProvider:
    def __init__(self):
        self.model_name = getattr(settings, 'PRODUCT_EMBEDDING_MODEL', 'intfloat/multilingual-e5-base')
        self.dimensions = int(getattr(settings, 'PRODUCT_EMBEDDING_DIMENSIONS', 768))
        self.device = getattr(settings, 'PRODUCT_EMBEDDING_DEVICE', 'cpu')

        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
        except Exception as exc:
            raise ImproperlyConfigured(
                f'Unable to load SentenceTransformer model "{self.model_name}". '
                'Install project requirements and ensure the model can be downloaded.'
            ) from exc

    def embed_texts(self, texts):
        vectors = self.model.encode(
            list(texts),
            batch_size=int(getattr(settings, 'RECOMMENDATION_EMBEDDING_BATCH_SIZE', 32)),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


def get_embedding_provider():
    return SentenceTransformerEmbeddingProvider()