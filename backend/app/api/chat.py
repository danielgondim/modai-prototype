"""Chat API routes – handles incoming messages and streams responses."""

import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message
from app.models.kanban import KanbanCard, KanbanColumn
from app.schemas import ChatRequest, ChatResponse, ConversationRead, MessageRead

router = APIRouter(prefix="/chat", tags=["Chat"])

# Tenant ID is hardcoded for prototype (single-tenant)
# In production, this would come from the WhatsApp webhook or auth token


@router.post("/message", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: uuid.UUID | None = None,
):
    """Process an incoming chat message and return AI response."""
    from app.services.chat_engine import process_message

    # For prototype: use first tenant if none specified
    if not tenant_id:
        from app.models.tenant import Tenant
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=500, detail="Nenhuma loja configurada")
        tenant_id = tenant.id

    # Find or create conversation
    conversation = None
    customer = None

    if body.conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == body.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            result = await db.execute(
                select(Customer).where(Customer.id == conversation.customer_id)
            )
            customer = result.scalar_one_or_none()

    if not conversation:
        # Create new customer
        customer = Customer(
            tenant_id=tenant_id,
            name=body.customer_name,
        )
        db.add(customer)
        await db.flush()

        # Create conversation
        conversation = Conversation(
            customer_id=customer.id,
            tenant_id=tenant_id,
        )
        db.add(conversation)
        await db.flush()

        # Create kanban card in first column
        first_col = await db.execute(
            select(KanbanColumn)
            .where(KanbanColumn.tenant_id == tenant_id)
            .order_by(KanbanColumn.position)
            .limit(1)
        )
        col = first_col.scalar_one_or_none()
        if col:
            card = KanbanCard(
                customer_id=customer.id,
                column_id=col.id,
                position=0,
            )
            db.add(card)
            await db.flush()

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    # Process with AI engine
    response = await process_message(
        db=db,
        conversation=conversation,
        customer=customer,
        user_message=body.message,
        tenant_id=tenant_id,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response["content"],
        tokens_input=response.get("tokens_input", 0),
        tokens_output=response.get("tokens_output", 0),
        model_used=response.get("model_used"),
        from_cache=response.get("from_cache", False),
    )
    db.add(assistant_msg)

    # Update conversation
    conversation.total_tokens_used += response.get("tokens_input", 0) + response.get("tokens_output", 0)
    conversation.last_message_at = datetime.now(timezone.utc)
    if response.get("new_stage"):
        conversation.current_stage = response["new_stage"]

    # Update customer last contact
    if customer:
        customer.last_contact = datetime.now(timezone.utc)
        if response.get("customer_updates"):
            for k, v in response["customer_updates"].items():
                if hasattr(customer, k):
                    setattr(customer, k, v)

    await db.flush()

    return ChatResponse(
        conversation_id=conversation.id,
        customer_id=customer.id if customer else conversation.customer_id,
        message=response["content"],
        stage=str(conversation.current_stage.value if hasattr(conversation.current_stage, 'value') else conversation.current_stage),
        model_used=response.get("model_used"),
        from_cache=response.get("from_cache", False),
        tokens_used=response.get("tokens_input", 0) + response.get("tokens_output", 0),
    )


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: uuid.UUID | None = None,
):
    """List all conversations (for CRM view)."""
    from app.models.tenant import Tenant
    if not tenant_id:
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if tenant:
            tenant_id = tenant.id

    result = await db.execute(
        select(Conversation)
        .where(Conversation.tenant_id == tenant_id)
        .order_by(Conversation.last_message_at.desc().nullslast())
    )
    return [ConversationRead.model_validate(c) for c in result.scalars().all()]


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageRead])
async def get_messages(
    conv_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all messages in a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    return [MessageRead.model_validate(m) for m in result.scalars().all()]
