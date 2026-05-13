"""Shared embedding utility – used by both RAG and semantic cache.

Supports Gemini (primary) and OpenAI (fallback) embedding providers.
Dimension is fixed at 3072 to match gemini-embedding-001.
"""

from app.config import get_settings

settings = get_settings()

EMBEDDING_DIM = 3072  # Gemini embedding-001 = 3072


async def get_embedding(text: str) -> list[float] | None:
    """Generate an embedding vector for the given text.

    Tries Gemini first, falls back to OpenAI.
    Returns a list of floats (dimension = EMBEDDING_DIM) or None on failure.
    """
    # Try Gemini first (free tier available)
    if settings.GOOGLE_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
            return list(result.embeddings[0].values)
        except Exception as e:
            print(f"Gemini embedding error: {e}")

    # Fallback to OpenAI
    if settings.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.embeddings.create(
                model="text-embedding-3-large",
                input=text,
                dimensions=EMBEDDING_DIM,
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")

    return None
