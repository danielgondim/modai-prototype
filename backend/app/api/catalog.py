"""Catalog CRUD routes."""

import uuid
import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.catalog import Catalog
from app.schemas import CatalogCreate, CatalogUpdate, CatalogRead

router = APIRouter(prefix="/catalogs", tags=["Catalogs"])


@router.get("/", response_model=list[CatalogRead])
async def list_catalogs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Catalog)
        .where(Catalog.tenant_id == current_user.tenant_id)
        .order_by(Catalog.name)
    )
    return [CatalogRead.model_validate(c) for c in result.scalars().all()]


@router.post("/", response_model=CatalogRead, status_code=201)
async def create_catalog(
    body: CatalogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    catalog = Catalog(
        tenant_id=current_user.tenant_id,
        name=body.name,
        description=body.description,
    )
    db.add(catalog)
    await db.flush()
    await db.refresh(catalog)
    return CatalogRead.model_validate(catalog)


@router.get("/{catalog_id}", response_model=CatalogRead)
async def get_catalog(
    catalog_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Catalog).where(
            Catalog.id == catalog_id, Catalog.tenant_id == current_user.tenant_id
        )
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo não encontrado")
    return CatalogRead.model_validate(catalog)


@router.put("/{catalog_id}", response_model=CatalogRead)
async def update_catalog(
    catalog_id: uuid.UUID,
    body: CatalogUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Catalog).where(
            Catalog.id == catalog_id, Catalog.tenant_id == current_user.tenant_id
        )
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo não encontrado")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(catalog, field, value)

    await db.flush()
    await db.refresh(catalog)
    return CatalogRead.model_validate(catalog)


@router.delete("/{catalog_id}", status_code=204)
async def delete_catalog(
    catalog_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Catalog).where(
            Catalog.id == catalog_id, Catalog.tenant_id == current_user.tenant_id
        )
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo não encontrado")
    await db.delete(catalog)


@router.post("/{catalog_id}/upload-pdf", response_model=CatalogRead)
async def upload_catalog_pdf(
    catalog_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um PDF")

    result = await db.execute(
        select(Catalog).where(
            Catalog.id == catalog_id, Catalog.tenant_id == current_user.tenant_id
        )
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo não encontrado")

    # Save file
    file_path = os.path.join("uploads", f"catalog_{catalog_id}.pdf")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    catalog.pdf_url = f"/uploads/catalog_{catalog_id}.pdf"
    await db.flush()
    await db.refresh(catalog)
    return CatalogRead.model_validate(catalog)


@router.post("/reindex", status_code=200)
async def reindex_products(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reindex all products for RAG vector search.

    Call this after adding/updating products or stock to refresh
    the vector embeddings used for semantic product retrieval.
    """
    from app.services.rag_service import index_all_products
    count = await index_all_products(db, current_user.tenant_id)
    return {"message": f"Reindexed {count} products", "indexed": count}

