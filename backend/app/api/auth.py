"""Auth routes – login and registration."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.auth import hash_password, verify_password, create_access_token
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    token = create_access_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    return TokenResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )


@router.post("/register", response_model=UserRead, status_code=201)
async def register(body: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserRead.model_validate(user)
