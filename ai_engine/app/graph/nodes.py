"""Graph Nodes – each function is a node in the LangGraph chat pipeline.

Every node receives the full ChatState and returns a partial dict
that gets merged back. Nodes use LangChain ChatModels with automatic
fallback (OpenAI ↔ Gemini) and LangSmith tracing.
"""

from app.config import get_settings
from app.graph.state import ChatState
from app.graph.llm import get_chat_model, get_fast_model
from app.cache_service import get_cached_response, cache_response
from app.rag_service import retrieve_with_fresh_stock
from app.ai.prompts import SYSTEM_PROMPT_TEMPLATE, STAGE_CLASSIFIER_PROMPT
from langchain_core.runnables import RunnableConfig

settings = get_settings()


def _calculate_model_cost(model_name: str, tokens_in: int, tokens_out: int) -> float:
    """Calculate the USD cost of an LLM call based on token usage.
    Prices are per 1M tokens (estimates).
    """
    model_name = model_name.lower()
    
    # Pricing per 1M tokens
    PRICES = {
        "gpt-4o": {"in": 5.0, "out": 15.0},
        "gpt-4o-mini": {"in": 0.15, "out": 0.60},
        "gemini-2.5-flash": {"in": 0.075, "out": 0.30},
        "gemini-2.0-flash": {"in": 0.075, "out": 0.30},
        "gemini-1.5-flash": {"in": 0.075, "out": 0.30},
    }

    # Find the best match for the model name
    matched_price = None
    for key, price in PRICES.items():
        if key in model_name:
            matched_price = price
            break
            
    if not matched_price:
        # Default to gpt-4o-mini prices if unknown
        matched_price = PRICES["gpt-4o-mini"]
        
    cost = (tokens_in * matched_price["in"] / 1_000_000) + (tokens_out * matched_price["out"] / 1_000_000)
    return cost


# ── Node 1: Check Semantic Cache ──────────────────────────────

async def check_cache_node(state: ChatState) -> dict:
    """Check if a semantically similar response exists in cache."""
    cached = await get_cached_response(
        tenant_id=state["tenant_id"],
        message=state["user_message"],
        stage=state["current_stage"],
    )
    if cached:
        return {
            "cached_response": cached,
            "response": cached["content"],
            "model_used": "cache",
            "tokens_input": 0,
            "tokens_output": 0,
            "from_cache": True,
        }
    return {"cached_response": None, "from_cache": False}


# ── Node 2: Classify Intent ──────────────────────────────────

async def classify_intent_node(state: ChatState) -> dict:
    """Classify whether the message needs product retrieval or is direct."""
    prompt = (
        "Classifique a intenção da mensagem do cliente.\n"
        "Se o cliente está perguntando sobre produtos, preços, disponibilidade, "
        "estoque, catálogo, ou quer comprar algo, responda: needs_products\n"
        "Se é uma saudação, despedida, agradecimento, pergunta sobre a loja, "
        "reclamação, ou conversa geral, responda: direct\n\n"
        f"Mensagem: \"{state['user_message']}\"\n"
        "Responda APENAS com needs_products ou direct."
    )
    tokens_in = 0
    tokens_out = 0
    try:
        model = get_fast_model()
        resp = await model.ainvoke(prompt)
        
        usage = getattr(resp, "usage_metadata", None)
        if usage:
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

        intent = resp.content.strip().lower()
        if intent not in ("needs_products", "direct"):
            intent = "needs_products"  # default to safe option
    except Exception as e:
        print(f"Intent classification error: {e}")
        intent = "needs_products"

    # Assume fast model is used (mini/flash)
    model_name = "gpt-4o-mini" # or gemini-flash
    cost = _calculate_model_cost(model_name, tokens_in, tokens_out)

    return {
        "intent": intent, 
        "tokens_input": tokens_in, 
        "tokens_output": tokens_out,
        "total_cost_usd": cost
    }


# ── Node 3: RAG Retrieve ─────────────────────────────────────

async def rag_retrieve_node(state: ChatState, config: RunnableConfig) -> dict:
    """Retrieve relevant products via vector similarity search."""
    products_context = await retrieve_with_fresh_stock(
        query=state["user_message"],
        tenant_id=state["tenant_id"],
    )
    return {"relevant_products": products_context}


# ── Node 4: Generate Response ────────────────────────────────

async def generate_response_node(state: ChatState) -> dict:
    """Generate the AI response using the full context."""
    # Build the system prompt
    if state.get("intent") == "direct":
        catalog_section = ""
    else:
        products = state.get("relevant_products")
        if products and products != "Catálogo não disponível":
            catalog_section = (
                "\n## Produtos Relevantes\n"
                "Os produtos abaixo foram selecionados como os mais relevantes para esta conversa.\n"
                "Se o cliente pedir algo que não está listado, informe que vai verificar com a equipe.\n"
                f"{products}\n"
            )
        else:
            catalog_section = (
                "\n## Produtos Relevantes\n"
                "Nenhum produto específico foi encontrado para esta busca.\n"
                "Informe ao cliente que não encontrou o que ele procura no momento.\n"
            )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        store_name=state.get("store_name", "Loja"),
        store_info=state.get("store_info", "Loja de confecções"),
        catalog_section=catalog_section,
        customer_info=state.get("customer_info", "Cliente novo"),
        conversation_context=state.get("conversation_context", ""),
    )

    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["user_message"]),
    ]

    model = get_chat_model(tier="standard")
    resp = await model.ainvoke(messages)

    # Extract token usage from response metadata
    tokens_in = 0
    tokens_out = 0
    usage = getattr(resp, "usage_metadata", None)
    if usage:
        tokens_in = usage.get("input_tokens", 0)
        tokens_out = usage.get("output_tokens", 0)

    model_name = getattr(resp, "response_metadata", {}).get("model_name", "unknown")
    cost = _calculate_model_cost(model_name, tokens_in, tokens_out)

    return {
        "response": resp.content,
        "model_used": model_name,
        "tokens_input": tokens_in,
        "tokens_output": tokens_out,
        "total_cost_usd": cost,
    }


# ── Node 5: Classify Stage ───────────────────────────────────

async def classify_stage_node(state: ChatState) -> dict:
    """Classify the conversation stage based on the message."""
    prompt = STAGE_CLASSIFIER_PROMPT.format(
        message=state["user_message"],
        current_stage=state["current_stage"],
    )
    tokens_in = 0
    tokens_out = 0
    try:
        model = get_fast_model()
        resp = await model.ainvoke(prompt)

        usage = getattr(resp, "usage_metadata", None)
        if usage:
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

        stage = resp.content.strip().lower()

        model_name = "gpt-4o-mini"
        cost = _calculate_model_cost(model_name, tokens_in, tokens_out)

        valid_stages = ["lead", "negociacao", "fechado", "perdido"] # Hardcoded for isolation
        update = {"tokens_input": tokens_in, "tokens_output": tokens_out, "total_cost_usd": cost}
        if stage in valid_stages:
            update["new_stage"] = stage
            return update
        update["new_stage"] = state["current_stage"]
        return update
    except Exception as e:
        print(f"Stage classification error: {e}")
        return {"new_stage": None, "tokens_input": tokens_in, "tokens_output": tokens_out, "total_cost_usd": 0.0}


# ── Node 6: Extract Customer Name ────────────────────────────

async def extract_name_node(state: ChatState) -> dict:
    """Extract customer name from the message if not yet known."""
    customer_updates = {}
    name = state.get("customer_name")
    if name and name.lower() != "cliente anônimo":
        return {"customer_updates": customer_updates}

    prompt = (
        "Você é um assistente responsável por extrair o nome de um cliente "
        "a partir de uma mensagem de chat.\n"
        "O cliente enviou a seguinte mensagem. Se ele estiver se apresentando "
        "ou informando o nome dele (ex: 'meu nome é Daniel', 'sou a Maria', "
        "'João', etc), responda EXATAMENTE com o primeiro nome dele com a "
        "primeira letra maiúscula e nada mais. Se não houver nenhum nome "
        "identificável na mensagem, responda EXATAMENTE com a palavra NONE.\n\n"
        f"Mensagem: '{state['user_message']}'"
    )
    tokens_in = 0
    tokens_out = 0
    try:
        model = get_fast_model()
        resp = await model.ainvoke(prompt)

        usage = getattr(resp, "usage_metadata", None)
        if usage:
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

        text = resp.content.strip()
        if text.upper() != "NONE" and len(text) < 20:
            customer_updates["name"] = text.replace(".", "").replace(",", "").title()
    except Exception as e:
        print(f"Name extraction error: {e}")

    cost = _calculate_model_cost("gpt-4o-mini", tokens_in, tokens_out)
    return {
        "customer_updates": customer_updates, 
        "tokens_input": tokens_in, 
        "tokens_output": tokens_out,
        "total_cost_usd": cost
    }


# ── Node 7: Persist (cache + token recording placeholder) ────

async def persist_node(state: ChatState) -> dict:
    """Cache the response for future semantic matches."""
    if state.get("from_cache"):
        return {}

    effective_stage = state.get("new_stage") or state["current_stage"]
    await cache_response(
        tenant_id=state["tenant_id"],
        message=state["user_message"],
        stage=effective_stage,
        response_content=state["response"],
        model_used=state.get("model_used", "unknown"),
    )
    return {}
