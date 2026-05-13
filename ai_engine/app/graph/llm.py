"""LLM Factory – creates LangChain ChatModels with automatic fallback.

Provides dual-provider support: OpenAI ↔ Gemini. If the primary provider
fails, the fallback kicks in automatically via LangChain's with_fallbacks().
All calls are automatically traced to LangSmith when LANGCHAIN_TRACING_V2=true.
"""

from functools import lru_cache
from app.config import get_settings

settings = get_settings()


def _setup_langsmith():
    """Configure LangSmith environment variables for tracing."""
    import os
    if settings.LANGSMITH_API_KEY and settings.LANGCHAIN_TRACING_V2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        print(f"🔭 LangSmith tracing enabled → project: {settings.LANGSMITH_PROJECT} at {settings.LANGSMITH_ENDPOINT}")


_setup_langsmith()


def get_chat_model(tier: str = "standard"):
    """Get a chat model with automatic fallback.

    Args:
        tier: "standard" for normal responses, "premium" for complex queries.

    Returns:
        A LangChain ChatModel (with fallback if both providers configured).
    """
    models = []

    if settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        model_name = "gpt-4o" if tier == "premium" else "gpt-4o-mini"
        models.append(ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=500,
        ))

    if settings.GOOGLE_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        models.append(ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=500,
        ))

    if not models:
        raise ValueError("No AI provider configured. Set OPENAI_API_KEY or GOOGLE_API_KEY.")

    primary = models[0]
    if len(models) > 1:
        return primary.with_fallbacks(models[1:])
    return primary


def get_fast_model():
    """Get a cheap/fast model for classification and extraction tasks.

    Always uses the cheapest available model with low temperature.
    """
    models = []

    if settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        models.append(ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
            max_tokens=200,
        ))

    if settings.GOOGLE_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        models.append(ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
            max_output_tokens=200,
        ))

    if not models:
        raise ValueError("No AI provider configured.")

    primary = models[0]
    if len(models) > 1:
        return primary.with_fallbacks(models[1:])
    return primary
