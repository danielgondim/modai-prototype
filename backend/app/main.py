"""ModAI Backend – FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.api import auth, catalog, product, customer, kanban, admin, chat, internal

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown events."""
    # Startup: run migrations and seed if needed
    from app.seed import seed_if_empty
    await seed_if_empty()
    yield
    # Shutdown: cleanup


# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="ModAI API",
    description="Chatbot de vendas com IA para lojas de confecção",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for PDF uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(product.router, prefix="/api")
app.include_router(customer.router, prefix="/api")
app.include_router(kanban.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(internal.router, prefix="/internal")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ModAI API"}
