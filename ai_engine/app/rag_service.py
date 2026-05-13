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
from redis.commands.search.query import Query

from app.config import get_settings
from app.embeddings import get_embedding, EMBEDDING_DIM

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
        if "vector blob size" in str(e):
            print(f"⚠️ RAG dimension mismatch. Resetting index {RAG_INDEX}...")
            try:
                redis = await _get_redis()
                await redis.ft(RAG_INDEX).dropindex(delete_documents=True)
            except:
                pass
        
        import traceback
        traceback.print_exc()
        print(f"RAG retrieval error: {e}")
        return []


async def retrieve_with_fresh_stock(
    query: str, tenant_id: str, top_k: int | None = None,
) -> str:
    """Retrieve relevant products.
    Returns a formatted string ready for injection into the LLM prompt.
    """
    products = await retrieve_relevant(query, tenant_id, top_k)
    if not products:
        return "Nenhum produto relevante encontrado no catálogo."

    import os
    import httpx
    import asyncio
    
    product_ids = [p["product_id"] for p in products]
    stock_map = {}
    
    # Tentativa de buscar estoque fresco do Core Backend
    backend_url = os.getenv("CORE_BACKEND_URL", "http://backend:8000")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{backend_url}/internal/stock", json={"product_ids": product_ids}, timeout=2.0)
            if resp.status_code == 200:
                stock_map = resp.json()
    except Exception as e:
        print(f"Could not fetch fresh stock: {e}")

    # Build formatted context
    lines = []
    for p in products:
        pid = p["product_id"]
        lines.append(f"\n### {p['name']} (Categoria: {p['category']})")

        # Use indexed text but replace stock with fresh data if available
        base_lines = p["text"].split("\n")
        for bl in base_lines:
            if bl.startswith("Estoque:"):
                continue
            
            # Truncate long lines (like descriptions) to save tokens
            if len(bl) > 80 and not bl.startswith("Produto:") and not bl.startswith("Preço:"):
                lines.append(bl[:80] + "...")
            else:
                lines.append(bl)

        if pid in stock_map:
            stock_items = stock_map[pid]
            stock_parts = []
            for si in stock_items:
                if si.get("quantity", 0) > 0:
                    stock_parts.append(f"{si.get('size', '')}/{si.get('color', '')}: {si.get('quantity', 0)} un.")
            if stock_parts:
                lines.append(f"Estoque: {', '.join(stock_parts)}")
            else:
                lines.append("Estoque: SEM ESTOQUE")
        else:
            # Fallback para o texto base que estava no Redis
            for bl in base_lines:
                if bl.startswith("Estoque:"):
                    lines.append(bl)

    return "\n".join(lines)
