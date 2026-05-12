"""Customer management routes."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.customer import Customer
from app.schemas import CustomerCreate, CustomerUpdate, CustomerRead

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=list[CustomerRead])
async def list_customers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Customer)
        .where(Customer.tenant_id == current_user.tenant_id)
        .order_by(Customer.last_contact.desc().nullslast())
    )
    return [CustomerRead.model_validate(c) for c in result.scalars().all()]


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return CustomerRead.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: uuid.UUID,
    body: CustomerUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == current_user.tenant_id,
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)

    await db.flush()
    await db.refresh(customer)
    return CustomerRead.model_validate(customer)
