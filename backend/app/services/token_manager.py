"""Token Manager – tracks usage and enforces limits per conversation/tenant."""

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_usage import TokenUsage, TokenLimit
from app.models.conversation import Conversation, ConversationStatus
from app.config import get_settings

settings = get_settings()

# Cost per million tokens (approximate)
MODEL_COSTS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
}


async def check_token_limit(
    db: AsyncSession,
    conversation: Conversation,
    tenant_id: uuid.UUID,
) -> dict:
    """Check if conversation has exceeded its token limit.

    Returns: {"exceeded": bool, "remaining": int, "limit": int}
    """
    # Get active limit for tenant
    result = await db.execute(
        select(TokenLimit).where(
            TokenLimit.tenant_id == tenant_id,
            TokenLimit.is_active == True,
        ).order_by(TokenLimit.created_at.desc()).limit(1)
    )
    limit = result.scalar_one_or_none()

    if not limit:
        # No limit set, use defaults
        max_tokens = settings.DEFAULT_MAX_TOKENS_PER_CHAT
        window_hours = settings.DEFAULT_TOKEN_WINDOW_HOURS
    else:
        max_tokens = limit.max_tokens_per_chat
        window_hours = limit.window_hours

    # Calculate tokens used in current window
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    tokens_used = conversation.total_tokens_used

    remaining = max_tokens - tokens_used
    exceeded = remaining <= 0

    return {
        "exceeded": exceeded,
        "remaining": max(0, remaining),
        "limit": max_tokens,
        "window_hours": window_hours,
    }


async def record_token_usage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    conversation_id: uuid.UUID,
    tokens_input: int,
    tokens_output: int,
    model_used: str,
):
    """Record token usage for billing and monitoring."""
    costs = MODEL_COSTS.get(model_used, {"input": 0.15, "output": 0.60})
    cost_usd = (
        (tokens_input / 1_000_000) * costs["input"]
        + (tokens_output / 1_000_000) * costs["output"]
    )

    usage = TokenUsage(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        model_used=model_used,
        cost_usd=cost_usd,
    )
    db.add(usage)


HANDOFF_MESSAGE = (
    "Olá! 😊 Nosso atendimento automático está sendo processado. "
    "Um de nossos atendentes vai te responder em instantes! "
    "Fique tranquilo(a), estamos aqui para te ajudar."
)
