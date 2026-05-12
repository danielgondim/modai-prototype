"""RAG Service – indexes products as vectors and retrieves relevant ones.

Architecture:
  1. Products are converted to text chunks and embedded using shared embeddings.
  2. Vectors are stored in Redis Stack with RediSearch index.
  3. On query, top-K products are retrieved via KNN cosine similarity.
  4. Fresh stock data is fetched from PostgreSQL for the matched products.
"""

import json
import numpy as np
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField, TagField, NumericField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.services.embeddings import get_embedding, EMBEDDING_DIM
from app.models.product import Product
from app.models.stock import StockItem
from app.models.catalog import Catalog

settings = get_settings()

RAG_INDEX = "idx:product_vectors"
RAG_PREFIX = "prod:"

_redis_client: Redis | None = None


async def _get_redis() -> Redis:
    """Get or create a Redis async connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_client


async def _ensure_rag_index():
    """Create the RediSearch product vector index if it doesn't exist."""
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
        print(f"✅ Created RAG index: {RAG_INDEX}")


def _product_to_text(product: Product, catalog_name: str, stock_items: list) -> str:
    """Convert a product + stock into a searchable text chunk."""
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
    """Index a single product as a vector in Redis."""
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
    """Reindex all active products for a tenant. Returns count indexed."""
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

    print(f"✅ Indexed {count} products for RAG (tenant={tenant_id})")
    return count


async def retrieve_relevant(query: str, tenant_id: str, top_k: int | None = None) -> list[dict]:
    """Retrieve top-K relevant products via vector similarity search."""
    if top_k is None:
        top_k = settings.RAG_TOP_K

    try:
        await _ensure_rag_index()
        embedding = await get_embedding(query)
        if not embedding:
            return []

        query_vector = np.array(embedding, dtype=np.float32).tobytes()
        clean_tenant = str(tenant_id).replace("-", "")

        q = (
            Query(
                f"(@tenant_id:{{{clean_tenant}}}) => "
                f"[KNN {top_k} @embedding $vec AS score]"
            )
            .sort_by("score")
            .return_fields("score", "product_id", "name", "text", "category", "price")
            .dialect(2)
        )

        redis = await _get_redis()
        results = await redis.ft(RAG_INDEX).search(q, query_params={"vec": query_vector})

        products = []
        for doc in results.docs:
            distance = float(doc.score)
            similarity = 1 - distance
            if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
                products.append({
                    "product_id": doc.product_id.decode() if isinstance(doc.product_id, bytes) else doc.product_id,
                    "name": doc.name.decode() if isinstance(doc.name, bytes) else doc.name,
                    "text": doc.text.decode() if isinstance(doc.text, bytes) else doc.text,
                    "category": doc.category.decode() if isinstance(doc.category, bytes) else doc.category,
                    "price": float(doc.price),
                    "similarity": similarity,
                })

        print(f"🔎 RAG: {len(products)} products found for '{query[:50]}...'")
        return products
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"RAG retrieval error: {e}")
        return []


async def retrieve_with_fresh_stock(
    query: str, tenant_id: str, db: AsyncSession, top_k: int | None = None,
) -> str:
    """Retrieve relevant products and enrich with fresh stock data from DB.

    Returns a formatted string ready for injection into the LLM prompt.
    """
    products = await retrieve_relevant(query, tenant_id, top_k)
    if not products:
        return "Nenhum produto relevante encontrado no catálogo."

    # Fetch fresh stock for matched product IDs
    import uuid as _uuid
    product_ids = []
    for p in products:
        try:
            product_ids.append(_uuid.UUID(p["product_id"]))
        except ValueError:
            pass

    stock_map: dict[str, list] = {}
    if product_ids:
        result = await db.execute(
            select(StockItem).where(StockItem.product_id.in_(product_ids))
        )
        for si in result.scalars().all():
            pid = str(si.product_id)
            stock_map.setdefault(pid, []).append(si)

    # Build formatted context
    lines = []
    for p in products:
        pid = p["product_id"]
        lines.append(f"\n### {p['name']} (Categoria: {p['category']})")

        # Use indexed text but replace stock with fresh data
        base_lines = p["text"].split("\n")
        for bl in base_lines:
            if bl.startswith("Estoque:"):
                continue
            
            # Truncate long lines (like descriptions) to save tokens
            if len(bl) > 80 and not bl.startswith("Produto:") and not bl.startswith("Preço:"):
                lines.append(bl[:80] + "...")
            else:
                lines.append(bl)

        # Fresh stock
        stock_items = stock_map.get(pid, [])
        stock_parts = []
        for si in stock_items:
            if si.quantity > 0:
                stock_parts.append(f"{si.size}/{si.color}: {si.quantity} un.")
        if stock_parts:
            lines.append(f"Estoque: {', '.join(stock_parts)}")
        else:
            lines.append("Estoque: SEM ESTOQUE")

    return "\n".join(lines)
