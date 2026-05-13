from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.database import get_db
from app.models.stock import StockItem

router = APIRouter()

class StockRequest(BaseModel):
    product_ids: List[str]

@router.post("/stock")
async def get_fresh_stock(req: StockRequest, db: AsyncSession = Depends(get_db)):
    """Fetch fresh stock for specific products (used internally by AI Orchestrator)."""
    valid_ids = []
    for pid in req.product_ids:
        try:
            valid_ids.append(uuid.UUID(pid))
        except:
            pass

    if not valid_ids:
        return {}

    result = await db.execute(
        select(StockItem).where(StockItem.product_id.in_(valid_ids))
    )
    
    stock_map = {}
    for si in result.scalars().all():
        pid_str = str(si.product_id)
        if pid_str not in stock_map:
            stock_map[pid_str] = []
        stock_map[pid_str].append({
            "size": si.size,
            "color": si.color,
            "quantity": si.quantity
        })

    return stock_map
