"""Graph Builder – assembles the LangGraph StateGraph for chat processing.

The graph routes messages through:
  check_cache → (hit? → extract_name → done)
              → classify_intent → (needs_products? → rag_retrieve)
              → generate → classify_stage → extract_name → persist → done
"""

from langgraph.graph import StateGraph, END
from app.graph.state import ChatState
from app.graph.nodes import (
    check_cache_node,
    classify_intent_node,
    rag_retrieve_node,
    generate_response_node,
    classify_stage_node,
    extract_name_node,
    persist_node,
)


def _route_after_cache(state: ChatState) -> str:
    """Route based on cache result: skip to extract_name or continue."""
    if state.get("from_cache"):
        return "extract_name"
    return "classify_intent"


def _route_by_intent(state: ChatState) -> str:
    """Route based on intent: needs product retrieval or direct response."""
    if state.get("intent") == "needs_products":
        return "rag_retrieve"
    return "generate"


def build_chat_graph() -> StateGraph:
    """Build and compile the chat processing graph.

    Returns a compiled LangGraph that can be invoked with:
        result = await graph.ainvoke(state, config={"configurable": {"db": db}})
    """
    builder = StateGraph(ChatState)

    # Add all nodes
    builder.add_node("check_cache", check_cache_node)
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("rag_retrieve", rag_retrieve_node)
    builder.add_node("generate", generate_response_node)
    builder.add_node("classify_stage", classify_stage_node)
    builder.add_node("extract_name", extract_name_node)
    builder.add_node("persist", persist_node)

    # Entry point
    builder.set_entry_point("check_cache")

    # Conditional: cache hit → extract_name, miss → classify_intent
    builder.add_conditional_edges("check_cache", _route_after_cache)

    # Conditional: needs_products → rag_retrieve, direct → generate
    builder.add_conditional_edges("classify_intent", _route_by_intent)

    # Linear edges
    builder.add_edge("rag_retrieve", "generate")
    builder.add_edge("generate", "classify_stage")
    builder.add_edge("classify_stage", "extract_name")
    builder.add_edge("extract_name", "persist")
    builder.add_edge("persist", END)

    return builder.compile()


# Singleton compiled graph
_graph = None


def get_chat_graph():
    """Get or create the compiled chat graph (singleton)."""
    global _graph
    if _graph is None:
        _graph = build_chat_graph()
    return _graph
