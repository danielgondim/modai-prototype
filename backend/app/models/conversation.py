"""Conversation model – a chat session between a customer and the bot."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"           # token limit hit, waiting for human
    HUMAN_TAKEOVER = "human_takeover"  # human operator responding
    CLOSED = "closed"


class ConversationStage(str, enum.Enum):
    GREETING = "greeting"
    BROWSING = "browsing"       # exploring catalog
    STOCK_CHECK = "stock_check" # asking about specific item availability
    ORDERING = "ordering"       # building an order
    CHECKOUT = "checkout"       # confirming order
    SUPPORT = "support"         # questions / complaints
    CLOSED = "closed"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.ACTIVE,
    )
    current_stage: Mapped[ConversationStage] = mapped_column(
        SAEnum(ConversationStage, name="conversation_stage"),
        default=ConversationStage.GREETING,
    )
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    context_summary: Mapped[dict | None] = mapped_column(
        JSONB, default=dict
    )  # compressed summary for sliding window
    order_data: Mapped[dict | None] = mapped_column(
        JSONB, default=dict
    )  # current order being built: {"items": [...], "total": 0}
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customer = relationship("Customer", back_populates="conversations", foreign_keys=[customer_id])
    tenant = relationship("Tenant", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
