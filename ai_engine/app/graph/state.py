"""Graph State – typed state definition for the LangGraph chat pipeline.

This TypedDict flows through every node. Each node reads what it needs
and returns a partial dict that gets merged back into the state.
"""

from __future__ import annotations
from typing import TypedDict, Annotated
import operator


class ChatState(TypedDict, total=False):
    # ── Inputs (set by the caller before graph invocation) ─────
    tenant_id: str
    conversation_id: str
    customer_id: str
    customer_name: str | None
    user_message: str
    current_stage: str
    store_name: str               # tenant name
    store_info: str              # tenant name + description
    customer_info: str           # name, age, preferences
    conversation_context: str    # sliding window of recent messages

    # ── Intermediary (set by nodes during processing) ──────────
    cached_response: dict | None   # from check_cache
    intent: str                    # from classify_intent: "needs_products" | "direct"
    relevant_products: str         # from rag_retrieve: formatted product context

    # ── Outputs (final result consumed by the caller) ──────────
    response: str
    new_stage: str | None
    model_used: str | None
    tokens_input: Annotated[int, operator.add]
    tokens_output: Annotated[int, operator.add]
    total_cost_usd: Annotated[float, operator.add]
    from_cache: bool
    customer_updates: dict

