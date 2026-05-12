"""Kanban models – columns and cards for customer pipeline management."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class KanbanColumn(Base):
    __tablename__ = "kanban_columns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # system columns cannot be deleted
    auto_stage: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # links to ConversationStage for auto-move
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # hex color
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="kanban_columns")
    cards = relationship("KanbanCard", back_populates="column", cascade="all, delete-orphan")


class KanbanCard(Base):
    __tablename__ = "kanban_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), unique=True, nullable=False
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kanban_columns.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    customer = relationship("Customer", back_populates="kanban_card")
    column = relationship("KanbanColumn", back_populates="cards")
