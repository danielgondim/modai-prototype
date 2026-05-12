"""Product and Stock routes."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.stock import StockItem
from app.models.catalog import Catalog
from app.schemas import (
    ProductCreate, ProductUpdate, ProductRead,
    StockItemCreate, StockItemUpdate, StockItemRead,
)

router = APIRouter(tags=["Products & Stock"])


# ── Products ──────────────────────────────────────────────────
@router.get("/products", response_model=list[ProductRead])
async def list_products(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    catalog_id: uuid.UUID | None = None,
):
    query = (
        select(Product)
        .join(Catalog)
        .where(Catalog.tenant_id == current_user.tenant_id)
    )
    if catalog_id:
        query = query.where(Product.catalog_id == catalog_id)
    result = await db.execute(query.order_by(Product.name))
    return [ProductRead.model_validate(p) for p in result.scalars().all()]


@router.post("/products", response_model=ProductRead, status_code=201)
async def create_product(
    body: ProductCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Verify catalog belongs to tenant
    cat = await db.execute(
        select(Catalog).where(
            Catalog.id == body.catalog_id,
            Catalog.tenant_id == current_user.tenant_id,
        )
    )
    if not cat.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Catálogo não encontrado")

    product = Product(**body.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ProductRead.model_validate(product)


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Product).join(Catalog).where(
            Product.id == product_id,
            Catalog.tenant_id == current_user.tenant_id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return ProductRead.model_validate(product)


@router.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Product).join(Catalog).where(
            Product.id == product_id,
            Catalog.tenant_id == current_user.tenant_id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return ProductRead.model_validate(product)


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Product).join(Catalog).where(
            Product.id == product_id,
            Catalog.tenant_id == current_user.tenant_id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    await db.delete(product)


# ── Stock ─────────────────────────────────────────────────────
@router.get("/products/{product_id}/stock", response_model=list[StockItemRead])
async def list_stock(
    product_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(StockItem).where(StockItem.product_id == product_id)
    )
    return [StockItemRead.model_validate(s) for s in result.scalars().all()]


@router.post("/stock", response_model=StockItemRead, status_code=201)
async def create_stock_item(
    body: StockItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    item = StockItem(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return StockItemRead.model_validate(item)


@router.put("/stock/{stock_id}", response_model=StockItemRead)
async def update_stock(
    stock_id: uuid.UUID,
    body: StockItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(StockItem).where(StockItem.id == stock_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado")
    item.quantity = body.quantity
    await db.flush()
    await db.refresh(item)
    return StockItemRead.model_validate(item)
