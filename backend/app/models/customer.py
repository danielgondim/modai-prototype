"""Customer model – end consumers who chat with the bot."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferences: Mapped[dict | None] = mapped_column(
        JSONB, default=dict
    )  # {"estilo": "casual", "tamanhos": ["M","G"], "cores_favoritas": ["azul","preto"]}
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_contact: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_contact: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan", foreign_keys="[Conversation.customer_id]")
    kanban_card = relationship("KanbanCard", back_populates="customer", uselist=False, cascade="all, delete-orphan")
