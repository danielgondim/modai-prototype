"""Kanban board routes – columns and cards."""

import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.kanban import KanbanColumn, KanbanCard
from app.schemas import (
    KanbanColumnCreate, KanbanColumnUpdate, KanbanColumnRead,
    KanbanCardRead, KanbanCardMove,
)

router = APIRouter(prefix="/kanban", tags=["Kanban"])


@router.get("/columns", response_model=list[KanbanColumnRead])
async def list_columns(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(KanbanColumn)
        .where(KanbanColumn.tenant_id == current_user.tenant_id)
        .options(selectinload(KanbanColumn.cards).selectinload(KanbanCard.customer))
        .order_by(KanbanColumn.position)
    )
    return [KanbanColumnRead.model_validate(c) for c in result.scalars().all()]


@router.post("/columns", response_model=KanbanColumnRead, status_code=201)
async def create_column(
    body: KanbanColumnCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Get max position
    result = await db.execute(
        select(KanbanColumn.position)
        .where(KanbanColumn.tenant_id == current_user.tenant_id)
        .order_by(KanbanColumn.position.desc())
        .limit(1)
    )
    max_pos = result.scalar_one_or_none() or 0

    col = KanbanColumn(
        tenant_id=current_user.tenant_id,
        name=body.name,
        color=body.color,
        position=max_pos + 1,
        is_system=False,
    )
    db.add(col)
    await db.flush()
    await db.refresh(col)
    return KanbanColumnRead.model_validate(col)


@router.put("/columns/{column_id}", response_model=KanbanColumnRead)
async def update_column(
    column_id: uuid.UUID,
    body: KanbanColumnUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(KanbanColumn).where(
            KanbanColumn.id == column_id,
            KanbanColumn.tenant_id == current_user.tenant_id,
        )
    )
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Coluna não encontrada")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(col, field, value)

    await db.flush()
    await db.refresh(col)
    return KanbanColumnRead.model_validate(col)


@router.delete("/columns/{column_id}", status_code=204)
async def delete_column(
    column_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(KanbanColumn).where(
            KanbanColumn.id == column_id,
            KanbanColumn.tenant_id == current_user.tenant_id,
        )
    )
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Coluna não encontrada")
    if col.is_system:
        raise HTTPException(status_code=400, detail="Colunas do sistema não podem ser removidas")
    await db.delete(col)


@router.put("/cards/{card_id}/move", response_model=KanbanCardRead)
async def move_card(
    card_id: uuid.UUID,
    body: KanbanCardMove,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(KanbanCard)
        .options(selectinload(KanbanCard.customer))
        .where(KanbanCard.id == card_id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado")

    card.column_id = body.column_id
    card.position = body.position
    card.moved_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(card)
    return KanbanCardRead.model_validate(card)
