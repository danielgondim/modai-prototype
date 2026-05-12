"""Seed data – fictional clothing store for the prototype."""

from sqlalchemy import select, text
from app.database import AsyncSessionLocal, engine, Base
from app.models import *
from app.models.user import UserRole
from app.auth import hash_password
from fpdf import FPDF
import os
import uuid


async def seed_if_empty():
    """Create tables and seed with fictional store data if DB is empty."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Tenant).limit(1))
        if result.scalar_one_or_none():
            return  # Already seeded

        # ── Tenant ────────────────────────────────────────────
        tenant = Tenant(
            name="Moda Estrela do Agreste",
            slug="moda-estrela",
            description=(
                "Loja de confecções localizada em Santa Cruz do Capibaribe, "
                "no coração do polo têxtil do Agreste Pernambucano. "
                "Trabalhamos com moda feminina, masculina e infantil, "
                "com preços de fábrica e qualidade premium. "
                "Funcionamos de segunda a sábado, das 8h às 18h. "
                "WhatsApp: (81) 99999-1234. "
                "Fazemos entregas para todo o Brasil via Correios e transportadora."
            ),
            settings={"currency": "BRL", "language": "pt-BR"},
        )
        db.add(tenant)
        await db.flush()

        # ── Users ─────────────────────────────────────────────
        admin_user = User(
            tenant_id=tenant.id,
            email="admin@modaestrela.com",
            name="Maria da Silva",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
        )
        superadmin = User(
            email="superadmin@modai.com",
            name="Admin ModAI",
            password_hash=hash_password("super123"),
            role=UserRole.SUPERADMIN,
        )
        db.add_all([admin_user, superadmin])
        await db.flush()
        # ── Catalogs ──────────────────────────────────────────
        def create_dummy_pdf(catalog_id: uuid.UUID, title: str, desc: str) -> str:
            os.makedirs("uploads", exist_ok=True)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            pdf.cell(200, 10, txt=f"Catálogo: {title}", ln=1, align="C")
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=desc, ln=1, align="C")
            pdf.cell(200, 10, txt="Confira nossos produtos acessando a loja!", ln=1, align="C")
            file_path = os.path.join("uploads", f"catalog_{catalog_id}.pdf")
            pdf.output(file_path)
            return f"/uploads/catalog_{catalog_id}.pdf"

        cat_blusas = Catalog(id=uuid.uuid4(), tenant_id=tenant.id, name="Blusas", description="Blusas femininas e masculinas")
        cat_calcas = Catalog(id=uuid.uuid4(), tenant_id=tenant.id, name="Calças", description="Calças jeans, sociais e esportivas")
        cat_vestidos = Catalog(id=uuid.uuid4(), tenant_id=tenant.id, name="Vestidos", description="Vestidos casuais e festivos")
        cat_camisas = Catalog(id=uuid.uuid4(), tenant_id=tenant.id, name="Camisas", description="Camisas polo, sociais e casuais")
        cat_shorts = Catalog(id=uuid.uuid4(), tenant_id=tenant.id, name="Shorts e Bermudas", description="Shorts e bermudas para todas as ocasiões")
        cat_intimas = Catalog(id=uuid.uuid4(), tenant_id=tenant.id, name="Roupas Íntimas", description="Cuecas, calcinhas e pijamas")

        catalogs = [cat_blusas, cat_calcas, cat_vestidos, cat_camisas, cat_shorts, cat_intimas]
        for c in catalogs:
            c.pdf_url = create_dummy_pdf(c.id, c.name, c.description or "")

        db.add_all(catalogs)
        await db.flush()

        # ── Products + Stock ──────────────────────────────────
        products_data = [
            # Blusas
            (cat_blusas.id, "Blusa Cropped Canelada", "Blusa cropped em malha canelada, super confortável", 39.90,
             {"material": "algodão canelado", "estilo": "casual"},
             [("P", "Branca", 15), ("M", "Branca", 20), ("G", "Branca", 10),
              ("P", "Preta", 12), ("M", "Preta", 18), ("G", "Preta", 8),
              ("P", "Rosa", 10), ("M", "Rosa", 15)]),

            (cat_blusas.id, "Blusa Manga Longa Básica", "Blusa manga longa em viscolycra", 49.90,
             {"material": "viscolycra", "estilo": "básico"},
             [("P", "Branca", 10), ("M", "Branca", 12), ("G", "Branca", 8), ("GG", "Branca", 5),
              ("P", "Preta", 10), ("M", "Preta", 15), ("G", "Preta", 10)]),

            (cat_blusas.id, "Regata Fitness Dry-Fit", "Regata para academia com tecido dry-fit", 34.90,
             {"material": "dry-fit", "estilo": "esportivo"},
             [("P", "Azul", 20), ("M", "Azul", 25), ("G", "Azul", 15),
              ("P", "Preta", 18), ("M", "Preta", 22)]),

            # Calças
            (cat_calcas.id, "Calça Jeans Skinny Feminina", "Calça jeans skinny com elastano", 89.90,
             {"material": "jeans com elastano", "estilo": "casual"},
             [("36", "Azul Escuro", 8), ("38", "Azul Escuro", 12), ("40", "Azul Escuro", 15),
              ("42", "Azul Escuro", 10), ("44", "Azul Escuro", 5),
              ("36", "Azul Claro", 6), ("38", "Azul Claro", 10), ("40", "Azul Claro", 12)]),

            (cat_calcas.id, "Calça Jeans Masculina Reta", "Calça jeans reta tradicional", 79.90,
             {"material": "jeans 100% algodão", "estilo": "tradicional"},
             [("38", "Azul Escuro", 10), ("40", "Azul Escuro", 15), ("42", "Azul Escuro", 12),
              ("44", "Azul Escuro", 8), ("46", "Azul Escuro", 5)]),

            (cat_calcas.id, "Calça Moletom Jogger", "Calça jogger em moletom peluciado", 69.90,
             {"material": "moletom peluciado", "estilo": "esportivo"},
             [("P", "Cinza", 10), ("M", "Cinza", 15), ("G", "Cinza", 12),
              ("P", "Preta", 8), ("M", "Preta", 12), ("G", "Preta", 10)]),

            # Vestidos
            (cat_vestidos.id, "Vestido Midi Floral", "Vestido midi estampado floral", 119.90,
             {"material": "viscose", "estilo": "romântico"},
             [("P", "Floral Azul", 5), ("M", "Floral Azul", 8), ("G", "Floral Azul", 4),
              ("P", "Floral Rosa", 6), ("M", "Floral Rosa", 10)]),

            (cat_vestidos.id, "Vestido Tubinho Preto", "Vestido tubinho clássico", 99.90,
             {"material": "crepe", "estilo": "elegante"},
             [("P", "Preto", 8), ("M", "Preto", 12), ("G", "Preto", 6), ("GG", "Preto", 3)]),

            # Camisas
            (cat_camisas.id, "Camisa Polo Masculina", "Camisa polo em piquet de algodão", 59.90,
             {"material": "piquet de algodão", "estilo": "casual"},
             [("P", "Branca", 10), ("M", "Branca", 15), ("G", "Branca", 12),
              ("P", "Azul Marinho", 8), ("M", "Azul Marinho", 12), ("G", "Azul Marinho", 10),
              ("P", "Vermelha", 5), ("M", "Vermelha", 8)]),

            (cat_camisas.id, "Camisa Social Slim", "Camisa social slim fit em tricoline", 89.90,
             {"material": "tricoline", "estilo": "social"},
             [("P", "Branca", 8), ("M", "Branca", 12), ("G", "Branca", 6),
              ("P", "Azul Claro", 6), ("M", "Azul Claro", 10)]),

            # Shorts
            (cat_shorts.id, "Short Jeans Feminino", "Short jeans desfiado", 59.90,
             {"material": "jeans", "estilo": "casual"},
             [("36", "Azul Médio", 10), ("38", "Azul Médio", 15), ("40", "Azul Médio", 12),
              ("42", "Azul Médio", 8)]),

            (cat_shorts.id, "Bermuda Tactel Masculina", "Bermuda tactel estampada", 44.90,
             {"material": "tactel", "estilo": "esportivo"},
             [("P", "Estampada Tropical", 12), ("M", "Estampada Tropical", 18),
              ("G", "Estampada Tropical", 10), ("P", "Preta", 8), ("M", "Preta", 12)]),

            # Roupas Íntimas
            (cat_intimas.id, "Kit 3 Cuecas Boxer", "Kit com 3 cuecas boxer em algodão", 49.90,
             {"material": "algodão", "estilo": "básico", "quantidade_kit": 3},
             [("P", "Sortidas", 15), ("M", "Sortidas", 20), ("G", "Sortidas", 12), ("GG", "Sortidas", 8)]),

            (cat_intimas.id, "Kit 5 Calcinhas Algodão", "Kit com 5 calcinhas em algodão", 39.90,
             {"material": "algodão", "estilo": "básico", "quantidade_kit": 5},
             [("P", "Sortidas", 20), ("M", "Sortidas", 25), ("G", "Sortidas", 15)]),
        ]

        for cat_id, name, desc, price, attrs, stock_data in products_data:
            prod = Product(
                catalog_id=cat_id, name=name, description=desc,
                price=price, attributes=attrs,
            )
            db.add(prod)
            await db.flush()

            for size, color, qty in stock_data:
                db.add(StockItem(product_id=prod.id, size=size, color=color, quantity=qty))

        # ── Kanban Columns ────────────────────────────────────
        columns = [
            ("Novos Clientes", 0, True, "greeting", "#6366f1"),
            ("Navegando", 1, True, "browsing", "#f59e0b"),
            ("Pedindo", 2, True, "ordering", "#3b82f6"),
            ("Comprando", 3, True, "checkout", "#10b981"),
            ("Suporte", 4, True, "support", "#ef4444"),
            ("Finalizados", 5, True, "closed", "#6b7280"),
        ]
        for name, pos, is_sys, stage, color in columns:
            db.add(KanbanColumn(
                tenant_id=tenant.id, name=name, position=pos,
                is_system=is_sys, auto_stage=stage, color=color,
            ))

        # ── Token Limit ───────────────────────────────────────
        db.add(TokenLimit(
            tenant_id=tenant.id,
            max_tokens_per_chat=50000,
            window_hours=72,
        ))

        await db.commit()
        print("✅ Seed data created: Moda Estrela do Agreste")

        # Index products for RAG (vector search)
        try:
            from app.services.rag_service import index_all_products
            count = await index_all_products(db, tenant.id)
            print(f"✅ RAG: Indexed {count} products for vector search")
        except Exception as e:
            print(f"⚠️  RAG indexing skipped (non-critical): {e}")

