"""Pydantic schemas for API request/response validation."""

from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Any


# ── Auth ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead | None = None


# ── Users ─────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "admin"


class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Tenants ───────────────────────────────────────────────────
class TenantCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    settings: dict | None
    ai_config: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Catalogs ──────────────────────────────────────────────────
class CatalogCreate(BaseModel):
    name: str
    description: str | None = None
    pdf_url: str | None = None


class CatalogUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    pdf_url: str | None = None
    is_active: bool | None = None


class CatalogRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    pdf_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Products ──────────────────────────────────────────────────
class ProductCreate(BaseModel):
    catalog_id: uuid.UUID
    name: str
    description: str | None = None
    price: float
    attributes: dict | None = None
    images: list[str] | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    attributes: dict | None = None
    images: list[str] | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: uuid.UUID
    catalog_id: uuid.UUID
    name: str
    description: str | None
    price: float
    attributes: dict | None
    images: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Stock ─────────────────────────────────────────────────────
class StockItemCreate(BaseModel):
    product_id: uuid.UUID
    size: str
    color: str
    quantity: int = 0


class StockItemUpdate(BaseModel):
    quantity: int


class StockItemRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    size: str
    color: str
    quantity: int
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Customers ─────────────────────────────────────────────────
class CustomerCreate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    age: int | None = None
    preferences: dict | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    age: int | None = None
    preferences: dict | None = None
    notes: str | None = None


class CustomerRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str | None
    phone: str | None
    email: str | None
    age: int | None
    preferences: dict | None
    notes: str | None
    first_contact: datetime
    last_contact: datetime | None

    model_config = {"from_attributes": True}


# ── Conversations ─────────────────────────────────────────────
class ConversationRead(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    current_stage: str
    total_tokens_used: int
    order_data: dict | None
    started_at: datetime
    last_message_at: datetime | None

    model_config = {"from_attributes": True}


# ── Messages ──────────────────────────────────────────────────
class MessageRead(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    tokens_input: int
    tokens_output: int
    model_used: str | None
    from_cache: bool
    from_human: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None
    customer_name: str | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    customer_id: uuid.UUID
    message: str
    stage: str
    model_used: str | None
    from_cache: bool
    tokens_used: int


# ── Kanban ────────────────────────────────────────────────────
class KanbanColumnCreate(BaseModel):
    name: str
    color: str | None = None


class KanbanColumnUpdate(BaseModel):
    name: str | None = None
    position: int | None = None
    color: str | None = None


class KanbanColumnRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    position: int
    is_system: bool
    auto_stage: str | None
    color: str | None
    cards: list[KanbanCardRead] = []

    model_config = {"from_attributes": True}


class KanbanCardRead(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    column_id: uuid.UUID
    position: int
    moved_at: datetime
    customer: CustomerRead | None = None

    model_config = {"from_attributes": True}


class KanbanCardMove(BaseModel):
    column_id: uuid.UUID
    position: int


# ── Token Admin ───────────────────────────────────────────────
class TokenLimitCreate(BaseModel):
    tenant_id: uuid.UUID
    max_tokens_per_chat: int = 50000
    window_hours: int = 72


class TokenLimitUpdate(BaseModel):
    max_tokens_per_chat: int | None = None
    window_hours: int | None = None
    is_active: bool | None = None


class TokenLimitRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    max_tokens_per_chat: int
    window_hours: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenUsageSummary(BaseModel):
    tenant_id: uuid.UUID
    tenant_name: str
    total_tokens_input: int
    total_tokens_output: int
    total_cost_usd: float
    period_start: datetime
    period_end: datetime


# Resolve forward references
TokenResponse.model_rebuild()
KanbanColumnRead.model_rebuild()
KanbanCardRead.model_rebuild()
