"""RAG Service (Backend) – indexes products as vectors.
Retrieval is handled by the AI Orchestrator service.
"""

import json
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField, TagField, NumericField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.services.embeddings import get_embedding, EMBEDDING_DIM
from app.models.product import Product
from app.models.catalog import Catalog

settings = get_settings()

RAG_INDEX = "idx:product_vectors"
RAG_PREFIX = "prod:"

_redis_client: Redis | None = None


async def _get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_client


async def _ensure_rag_index():
    redis = await _get_redis()
    try:
        await redis.ft(RAG_INDEX).info()
    except Exception:
        schema = (
            TagField("$.tenant_id", as_name="tenant_id"),
            TextField("$.name", as_name="name"),
            TextField("$.category", as_name="category"),
            TextField("$.text", as_name="text"),
            NumericField("$.price", as_name="price"),
            TextField("$.product_id", as_name="product_id"),
            VectorField(
                "$.embedding", "FLAT",
                {"TYPE": "FLOAT32", "DIM": EMBEDDING_DIM, "DISTANCE_METRIC": "COSINE"},
                as_name="embedding",
            ),
        )
        definition = IndexDefinition(prefix=[RAG_PREFIX], index_type=IndexType.JSON)
        await redis.ft(RAG_INDEX).create_index(fields=schema, definition=definition)


def _product_to_text(product: Product, catalog_name: str, stock_items: list) -> str:
    lines = [f"Produto: {product.name} | Categoria: {catalog_name}"]
    if product.description:
        lines.append(product.description)
    lines.append(f"Preço: R$ {float(product.price):.2f}")
    if product.attributes:
        attrs = " | ".join(f"{k}: {v}" for k, v in product.attributes.items())
        lines.append(attrs)
    stock_parts = []
    for si in stock_items:
        if si.quantity > 0:
            stock_parts.append(f"{si.size}/{si.color}({si.quantity})")
    if stock_parts:
        lines.append(f"Estoque: {' '.join(stock_parts)}")
    else:
        lines.append("Estoque: ESGOTADO")
    return "\n".join(lines)


async def index_product(
    product: Product, catalog_name: str, stock_items: list, tenant_id: str,
) -> bool:
    try:
        await _ensure_rag_index()
        text = _product_to_text(product, catalog_name, stock_items)
        embedding = await get_embedding(text)
        if not embedding:
            return False

        redis = await _get_redis()
        clean_tenant = str(tenant_id).replace("-", "")
        key = f"{RAG_PREFIX}{str(product.id).replace('-', '')}"

        data = {
            "tenant_id": clean_tenant,
            "product_id": str(product.id),
            "name": product.name,
            "category": catalog_name,
            "text": text,
            "price": float(product.price),
            "embedding": embedding,
        }
        await redis.json().set(key, "$", data)
        return True
    except Exception as e:
        print(f"Error indexing product {product.name}: {e}")
        return False


async def index_all_products(db: AsyncSession, tenant_id) -> int:
    result = await db.execute(
        select(Catalog)
        .where(Catalog.tenant_id == tenant_id, Catalog.is_active == True)
        .options(selectinload(Catalog.products).selectinload(Product.stock_items))
    )
    catalogs = result.scalars().all()

    count = 0
    for catalog in catalogs:
        for product in catalog.products:
            if not product.is_active:
                continue
            ok = await index_product(product, catalog.name, product.stock_items, str(tenant_id))
            if ok:
                count += 1
    return count
