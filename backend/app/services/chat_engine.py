"""Chat Engine – core AI processing pipeline.

Delegates AI orchestration to the LangGraph-based graph while handling
all database operations (context building, persistence, kanban updates).
"""

import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationStatus, ConversationStage
from app.models.customer import Customer
from app.models.message import Message
from app.models.tenant import Tenant
from app.models.kanban import KanbanCard, KanbanColumn
from app.services.token_manager import check_token_limit, record_token_usage, HANDOFF_MESSAGE
from app.services.graph.builder import get_chat_graph
from app.services.graph.llm import get_fast_model
from app.ai.prompts import SUMMARY_PROMPT
from app.config import get_settings

settings = get_settings()


async def process_message(
    db: AsyncSession,
    conversation: Conversation,
    customer: Customer,
    user_message: str,
    tenant_id: uuid.UUID,
) -> dict:
    """Process a user message and generate an AI response.

    Returns dict with: content, tokens_input, tokens_output,
    model_used, from_cache, new_stage, customer_updates
    """
    # 1. Check token limits (stays outside graph – needs DB)
    limit_status = await check_token_limit(db, conversation, tenant_id)
    if limit_status["exceeded"]:
        conversation.status = ConversationStatus.PAUSED
        return {
            "content": HANDOFF_MESSAGE,
            "tokens_input": 0,
            "tokens_output": 0,
            "model_used": None,
            "from_cache": False,
            "new_stage": None,
            "customer_updates": {},
        }

    # 2. Build context from DB (tenant, customer, messages)
    context = await _build_context(db, conversation, customer, tenant_id)

    # 3. Get current stage
    current_stage = (
        conversation.current_stage.value if hasattr(conversation.current_stage, 'value')
        else str(conversation.current_stage)
    )

    # 4. Invoke LangGraph
    graph = get_chat_graph()
    initial_state = {
        "tenant_id": str(tenant_id),
        "conversation_id": str(conversation.id),
        "customer_id": str(customer.id),
        "customer_name": customer.name,
        "user_message": user_message,
        "current_stage": current_stage,
        "store_name": context["store_name"],
        "store_info": context["store_info"],
        "customer_info": context["customer_info"],
        "conversation_context": context["conversation_context"],
    }

    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"db": db}},
    )

    # 5. Post-graph DB operations
    new_stage = result.get("new_stage")

    # Auto-move kanban card if stage changed
    if new_stage and new_stage != current_stage:
        await _auto_move_kanban(db, customer.id, tenant_id, new_stage)

    # Record token usage (only for non-cached responses)
    if not result.get("from_cache"):
        await record_token_usage(
            db, tenant_id, conversation.id,
            result.get("tokens_input", 0),
            result.get("tokens_output", 0),
            result.get("model_used", "unknown"),
        )

    # Summarize conversation history in the background (awaited)
    await _summarize_history(db, conversation)

    return {
        "content": result.get("response", "Desculpe, ocorreu um erro."),
        "tokens_input": result.get("tokens_input", 0),
        "tokens_output": result.get("tokens_output", 0),
        "model_used": result.get("model_used"),
        "from_cache": result.get("from_cache", False),
        "new_stage": new_stage,
        "customer_updates": result.get("customer_updates", {}),
    }


async def _build_context(
    db: AsyncSession,
    conversation: Conversation,
    customer: Customer,
    tenant_id: uuid.UUID,
) -> dict:
    """Build non-catalog context from the database.

    Catalog/product context is now handled by the RAG node in the graph.
    """
    # Get tenant info
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    store_info = tenant.description or "Loja de confecções" if tenant else "Loja de confecções"

    # Build customer info
    customer_info = "Cliente novo (sem informações prévias)"
    if customer and customer.name:
        parts = [f"Nome: {customer.name}"]
        if customer.age:
            parts.append(f"Idade: {customer.age}")
        if customer.preferences:
            parts.append(f"Preferências: {json.dumps(customer.preferences, ensure_ascii=False)}")
        customer_info = " | ".join(parts)

    # Get recent messages (sliding window)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(settings.CHAT_MAX_HISTORY_MESSAGES)
    )
    recent_msgs = list(reversed(result.scalars().all()))

    conversation_context = ""
    if conversation.context_summary:
        if isinstance(conversation.context_summary, dict) and "text" in conversation.context_summary:
            conversation_context = f"Resumo anterior: {conversation.context_summary['text']}\n\n"
        else:
            conversation_context = f"Resumo anterior: {json.dumps(conversation.context_summary, ensure_ascii=False)}\n\n"

    if recent_msgs:
        for msg in recent_msgs:
            role_label = "Cliente" if msg.role == "user" else "Vendedor"
            conversation_context += f"{role_label}: {msg.content}\n"

    return {
        "store_name": tenant.name if tenant else "Loja",
        "store_info": store_info,
        "customer_info": customer_info,
        "conversation_context": conversation_context,
    }


async def _auto_move_kanban(
    db: AsyncSession,
    customer_id: uuid.UUID,
    tenant_id: uuid.UUID,
    new_stage: str,
):
    """Automatically move a customer's kanban card based on conversation stage."""
    # Find the column mapped to this stage
    result = await db.execute(
        select(KanbanColumn).where(
            KanbanColumn.tenant_id == tenant_id,
            KanbanColumn.auto_stage == new_stage,
        )
    )
    target_column = result.scalar_one_or_none()
    if not target_column:
        return

    # Find the customer's card
    result = await db.execute(
        select(KanbanCard).where(KanbanCard.customer_id == customer_id)
    )
    card = result.scalar_one_or_none()
    if not card:
        return

    # Move card
    card.column_id = target_column.id
    card.moved_at = datetime.now(timezone.utc)


async def _summarize_history(db: AsyncSession, conversation: Conversation):
    """Summarize older messages if we exceed the max history size."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    all_msgs = result.scalars().all()
    
    if len(all_msgs) <= settings.CHAT_MAX_HISTORY_MESSAGES:
        return
        
    to_summarize = all_msgs[:-settings.CHAT_MAX_HISTORY_MESSAGES]
    
    summary_data = conversation.context_summary or {}
    last_id = summary_data.get("last_id")
    
    start_idx = 0
    if last_id:
        for i, m in enumerate(to_summarize):
            if str(m.id) == last_id:
                start_idx = i + 1
                break
                
    unsummarized = to_summarize[start_idx:]
    if not unsummarized:
        return
        
    text_to_summarize = ""
    for m in unsummarized:
        role = "Cliente" if m.role == "user" else "Vendedor"
        text_to_summarize += f"{role}: {m.content}\n"
        
    old_summary = summary_data.get("text", "")
    context_text = ""
    if old_summary:
        context_text += f"Resumo Anterior:\n{old_summary}\n\n"
    context_text += f"Novas Mensagens a sumarizar:\n{text_to_summarize}"
    
    prompt = SUMMARY_PROMPT.format(messages=context_text)
    
    try:
        model = get_fast_model()
        resp = await model.ainvoke(prompt)
        new_summary = resp.content.strip()
        
        # update the JSON dict in the model
        # Needs to assign a new dict so SQLAlchemy detects the change in JSONB
        conversation.context_summary = {
            "text": new_summary,
            "last_id": str(unsummarized[-1].id)
        }
    except Exception as e:
        print(f"Error summarizing conversation: {e}")
