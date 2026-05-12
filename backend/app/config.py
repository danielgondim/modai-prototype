"""ModAI Backend – Application Configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://modai:modai_secret@db:5432/modai"
    DATABASE_URL_SYNC: str = "postgresql://modai:modai_secret@db:5432/modai"

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── JWT ───────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    # ── AI Providers ──────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # ── App ───────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # ── Semantic Cache ────────────────────────────────────────
    CACHE_SIMILARITY_THRESHOLD: float = 0.90
    CACHE_TTL_FAQ_SECONDS: int = 86400     # 24h
    CACHE_TTL_STOCK_SECONDS: int = 300     # 5min

    # ── RAG ───────────────────────────────────────────────────
    RAG_TOP_K: int = 3
    RAG_SIMILARITY_THRESHOLD: float = 0.30

    # ── LangSmith Observability ───────────────────────────────
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "modai-chatbot"
    LANGCHAIN_TRACING_V2: bool = False

    # ── Token Limits (defaults) ───────────────────────────────
    DEFAULT_MAX_TOKENS_PER_CHAT: int = 50000
    DEFAULT_TOKEN_WINDOW_HOURS: int = 72   # 3 days

    # ── Chat Engine ───────────────────────────────────────────
    CHAT_MAX_HISTORY_MESSAGES: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
