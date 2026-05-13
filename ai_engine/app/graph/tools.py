"""Graph Tools – LangChain tools for future agent capabilities.

These tools can be bound to the LLM via model.bind_tools() when the
chatbot evolves into a full agent with tool-calling support.
For now they serve as the foundation for features like:
  - Real-time stock lookup
  - Order total calculation
  - Catalog PDF link retrieval
"""

from langchain_core.tools import tool


@tool
def consultar_estoque(produto: str, tamanho: str, cor: str) -> str:
    """Consulta estoque em tempo real de um produto específico.

    Args:
        produto: Nome do produto
        tamanho: Tamanho desejado (P, M, G, GG, 36, 38, etc.)
        cor: Cor desejada

    Returns:
        Informação sobre disponibilidade do produto.
    """
    # TODO: Implement with DB query when tool-calling is enabled
    return f"Verificando estoque de {produto} tamanho {tamanho} cor {cor}..."


@tool
def calcular_total_pedido(itens: list[dict]) -> str:
    """Calcula o total de um pedido com múltiplos itens.

    Args:
        itens: Lista de dicts com {nome, preco, quantidade}

    Returns:
        Resumo do pedido com total.
    """
    total = 0.0
    linhas = []
    for item in itens:
        subtotal = item.get("preco", 0) * item.get("quantidade", 1)
        total += subtotal
        linhas.append(f"- {item.get('nome', '?')} x{item.get('quantidade', 1)}: R$ {subtotal:.2f}")
    linhas.append(f"\nTotal: R$ {total:.2f}")
    return "\n".join(linhas)


@tool
def buscar_link_catalogo(categoria: str) -> str:
    """Retorna o link do PDF do catálogo de uma categoria.

    Args:
        categoria: Nome da categoria (ex: Blusas, Calças, Vestidos)

    Returns:
        Link do PDF ou mensagem informando que não foi encontrado.
    """
    # TODO: Implement with DB query when tool-calling is enabled
    return f"Buscando catálogo PDF da categoria {categoria}..."


# All available tools for future binding
AVAILABLE_TOOLS = [consultar_estoque, calcular_total_pedido, buscar_link_catalogo]
