"""Semantic Cache Service – caches AI responses using vector similarity in Redis.

Uses embedding vectors to find semantically similar questions that have already
been answered, avoiding redundant API calls to the LLM.

Architecture:
  1. Each cached response is stored as a Redis Hash with the embedding vector.
  2. RediSearch vector index enables cosine similarity search.
  3. On cache hit (similarity >= threshold), the stored response is returned
     with from_cache=True and zero token usage.
"""

import json
import hashlib
import numpy as np
from datetime import datetime, timezone
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField, NumericField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from app.config import get_settings
from app.services.embeddings import get_embedding, EMBEDDING_DIM


settings = get_settings()

CACHE_INDEX_NAME = "idx:semantic_cache"
CACHE_KEY_PREFIX = "cache:"

# Stages that are safe to cache (no order-specific data)
CACHEABLE_STAGES = {"greeting", "browsing", "support", "stock_check"}

# TTL by stage category
STAGE_TTL = {
    "greeting": settings.CACHE_TTL_FAQ_SECONDS,    # 24h
    "browsing": settings.CACHE_TTL_FAQ_SECONDS,     # 24h
    "support": settings.CACHE_TTL_FAQ_SECONDS,      # 24h
    "stock_check": settings.CACHE_TTL_STOCK_SECONDS, # 5min
}

_redis_client: Redis | None = None


async def _get_redis() -> Redis:
    """Get or create a Redis async connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # We need bytes for vectors
        )
    return _redis_client


async def _ensure_index():
    """Create the RediSearch vector index if it doesn't exist."""
    redis = await _get_redis()
    try:
        await redis.ft(CACHE_INDEX_NAME).info()
    except Exception:
        # Index doesn't exist, create it
        schema = (
            TagField("$.tenant_id", as_name="tenant_id"),
            TextField("$.stage", as_name="stage"),
            TextField("$.message", as_name="message"),
            TextField("$.response", as_name="response"),
            NumericField("$.created_at", as_name="created_at"),
            VectorField(
                "$.embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": EMBEDDING_DIM,
                    "DISTANCE_METRIC": "COSINE",
                },
                as_name="embedding",
            ),
        )
        definition = IndexDefinition(
            prefix=[CACHE_KEY_PREFIX],
            index_type=IndexType.JSON,
        )
        await redis.ft(CACHE_INDEX_NAME).create_index(
            fields=schema,
            definition=definition,
        )
        print(f"✅ Created Redis vector index: {CACHE_INDEX_NAME}")




async def get_cached_response(
    tenant_id: str,
    message: str,
    stage: str,
) -> dict | None:
    """Search for a semantically similar cached response.

    Returns a dict with {content, model_used} if found, None otherwise.
    """
    if stage not in CACHEABLE_STAGES:
        return None

    try:
        await _ensure_index()

        # Generate embedding for the incoming message
        embedding = await get_embedding(message)
        if not embedding:
            return None

        # Convert to bytes for Redis query
        query_vector = np.array(embedding, dtype=np.float32).tobytes()

        # Normalize tenant_id (remove hyphens for RediSearch compatibility)
        clean_tenant = tenant_id.replace("-", "")

        # Build KNN query filtered by tenant and stage
        q = (
            Query(
                f"(@tenant_id:{{{clean_tenant}}} @stage:{stage}) => "
                f"[KNN 3 @embedding $vec AS score]"
            )
            .sort_by("score")
            .return_fields("score", "message", "response", "stage")
            .dialect(2)
        )

        redis = await _get_redis()
        results = await redis.ft(CACHE_INDEX_NAME).search(
            q, query_params={"vec": query_vector}
        )

        if not results.docs:
            print(f"❌ Cache MISS: no entries found for tenant/stage")
            return None

        # Dynamic threshold based on stage to avoid false positives in critical stages
        thresholds = {
            "greeting": 0.80,     # Greetings can vary ("oi bom dia" vs "ola bom dia")
            "browsing": 0.90,     # Needs to be high to distinguish "azul" vs "preta"
            "stock_check": 0.93,  # Needs to be very high for exact sizes
            "support": 0.85,
        }
        threshold = thresholds.get(stage, settings.CACHE_SIMILARITY_THRESHOLD)

        best_doc = None
        best_sim = -1
        
        for doc in results.docs:
            doc_stage = doc.stage.decode() if isinstance(doc.stage, bytes) else doc.stage
            if doc_stage != stage:
                continue
            sim = 1 - float(doc.score)
            if sim > best_sim:
                best_sim = sim
                best_doc = doc

        if best_doc and best_sim >= threshold:
            response_data = json.loads(best_doc.response)
            orig_msg = best_doc.message.decode() if isinstance(best_doc.message, bytes) else best_doc.message
            print(
                f"🎯 Cache HIT! similarity={best_sim:.3f} "
                f"(threshold={threshold}) "
                f"original='{orig_msg}'"
            )
            return {
                "content": response_data["content"],
                "model_used": "cache",
                "similarity": best_sim,
            }

        print(
            f"❌ Cache MISS: max_similarity={best_sim:.3f} "
            f"< threshold={threshold}"
        )
        return None

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Cache lookup error: {e}")
        return None


async def cache_response(
    tenant_id: str,
    message: str,
    stage: str,
    response_content: str,
    model_used: str,
) -> bool:
    """Cache an AI response with its embedding vector.

    Returns True if successfully cached, False otherwise.
    """
    if stage not in CACHEABLE_STAGES:
        return False

    # Don't cache error messages
    if "dificuldade técnica" in response_content:
        return False

    try:
        await _ensure_index()

        # Generate embedding
        embedding = await get_embedding(message)
        if not embedding:
            return False

        # Create unique key
        key_hash = hashlib.md5(
            f"{tenant_id}:{message}".encode()
        ).hexdigest()
        redis_key = f"{CACHE_KEY_PREFIX}{key_hash}"

        # Store as JSON
        ttl = STAGE_TTL.get(stage, settings.CACHE_TTL_FAQ_SECONDS)
        data = {
            "tenant_id": str(tenant_id).replace("-", ""),
            "stage": stage,
            "message": message,
            "response": json.dumps({
                "content": response_content,
                "model_used": model_used,
            }),
            "embedding": embedding,
            "created_at": int(datetime.now(timezone.utc).timestamp()),
        }

        redis = await _get_redis()
        await redis.json().set(redis_key, "$", data)
        await redis.expire(redis_key, ttl)

        print(
            f"💾 Cached response for '{message[:50]}...' "
            f"(stage={stage}, ttl={ttl}s)"
        )
        return True

    except Exception as e:
        print(f"Cache store error: {e}")
        return False
