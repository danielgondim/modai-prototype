"""Model Router – selects the optimal AI model based on message complexity."""

import re
from app.config import get_settings

settings = get_settings()

# Keywords that indicate complex interactions requiring premium model
COMPLEX_KEYWORDS = [
    "reclamação", "reclamar", "problema", "defeito", "troca", "devolver",
    "devolução", "insatisfeito", "insatisfação", "raiva", "absurdo",
    "negociar", "desconto", "parcelar", "parcelas", "negociação",
    "comparar", "diferença entre", "qual melhor", "me ajude a escolher",
    "personalizar", "personalizado", "sob medida", "encomenda",
]

# Keywords that indicate simple interactions suitable for cheaper model
SIMPLE_KEYWORDS = [
    "oi", "olá", "bom dia", "boa tarde", "boa noite", "tudo bem",
    "obrigado", "obrigada", "tchau", "até mais", "valeu",
    "preço", "quanto custa", "tem", "disponível", "estoque",
    "tamanho", "cor", "cores", "horário", "endereço", "localização",
    "entrega", "frete", "prazo",
]


def classify_complexity(message: str) -> str:
    """Classify message complexity: 'simple', 'complex', or 'medium'.

    Returns the recommended model tier.
    """
    msg_lower = message.lower().strip()

    # Very short messages are almost always simple
    if len(msg_lower.split()) <= 3:
        return "simple"

    # Check for complex keywords
    complex_score = sum(1 for kw in COMPLEX_KEYWORDS if kw in msg_lower)
    simple_score = sum(1 for kw in SIMPLE_KEYWORDS if kw in msg_lower)

    # Long messages with questions tend to be more complex
    question_marks = msg_lower.count("?")
    if question_marks >= 2:
        complex_score += 1

    # Messages with multiple sentences tend to be more complex
    sentences = len(re.split(r'[.!?]+', msg_lower))
    if sentences >= 3:
        complex_score += 1

    if complex_score >= 2:
        return "complex"
    elif complex_score >= 1 and simple_score == 0:
        return "complex"
    else:
        return "simple"


def select_model(complexity: str) -> dict:
    """Select the appropriate model based on complexity.

    Returns dict with provider and model name.
    """
    if complexity == "complex":
        if settings.OPENAI_API_KEY:
            return {"provider": "openai", "model": "gpt-4o"}
        elif settings.GOOGLE_API_KEY:
            return {"provider": "gemini", "model": "gemini-2.5-flash"}
    else:  # simple or medium
        if settings.OPENAI_API_KEY:
            return {"provider": "openai", "model": "gpt-4o-mini"}
        elif settings.GOOGLE_API_KEY:
            return {"provider": "gemini", "model": "gemini-2.5-flash"}

    # Fallback
    return {"provider": "openai", "model": "gpt-4o-mini"}
