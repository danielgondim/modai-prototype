"""Tenant model – each clothing store is a tenant."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    ai_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    catalogs = relationship("Catalog", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    kanban_columns = relationship("KanbanColumn", back_populates="tenant", cascade="all, delete-orphan")
    token_usages = relationship("TokenUsage", back_populates="tenant", cascade="all, delete-orphan")
    token_limits = relationship("TokenLimit", back_populates="tenant", cascade="all, delete-orphan")
