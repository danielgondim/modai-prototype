"""Admin routes – token usage monitoring and limit management."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.user import User
from app.models.tenant import Tenant
from app.models.token_usage import TokenUsage, TokenLimit
from app.schemas import (
    TokenLimitCreate, TokenLimitUpdate, TokenLimitRead,
    TokenUsageSummary, TenantRead,
)

router = APIRouter(prefix="/admin", tags=["Admin ModAI"])


@router.get("/tenants", response_model=list[TenantRead])
async def list_tenants(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Tenant).order_by(Tenant.name))
    return [TenantRead.model_validate(t) for t in result.scalars().all()]


@router.get("/tokens/usage")
async def get_token_usage(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            TokenUsage.tenant_id,
            Tenant.name.label("tenant_name"),
            func.sum(TokenUsage.tokens_input).label("total_input"),
            func.sum(TokenUsage.tokens_output).label("total_output"),
            func.coalesce(func.sum(TokenUsage.cost_usd), 0).label("total_cost"),
        )
        .join(Tenant, TokenUsage.tenant_id == Tenant.id)
        .where(TokenUsage.recorded_at >= since)
        .group_by(TokenUsage.tenant_id, Tenant.name)
    )
    now = datetime.now(timezone.utc)
    return [
        TokenUsageSummary(
            tenant_id=r.tenant_id, tenant_name=r.tenant_name,
            total_tokens_input=r.total_input or 0,
            total_tokens_output=r.total_output or 0,
            total_cost_usd=float(r.total_cost or 0),
            period_start=since, period_end=now,
        ) for r in result.all()
    ]


@router.get("/tokens/limits", response_model=list[TokenLimitRead])
async def list_token_limits(
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(TokenLimit))
    return [TokenLimitRead.model_validate(t) for t in result.scalars().all()]


@router.post("/tokens/limits", response_model=TokenLimitRead, status_code=201)
async def create_token_limit(
    body: TokenLimitCreate,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    limit = TokenLimit(**body.model_dump())
    db.add(limit)
    await db.flush()
    await db.refresh(limit)
    return TokenLimitRead.model_validate(limit)


@router.put("/tokens/limits/{limit_id}", response_model=TokenLimitRead)
async def update_token_limit(
    limit_id: uuid.UUID, body: TokenLimitUpdate,
    current_user: Annotated[User, Depends(require_superadmin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(TokenLimit).where(TokenLimit.id == limit_id))
    limit = result.scalar_one_or_none()
    if not limit:
        raise HTTPException(status_code=404, detail="Limite não encontrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(limit, field, value)
    await db.flush()
    await db.refresh(limit)
    return TokenLimitRead.model_validate(limit)
