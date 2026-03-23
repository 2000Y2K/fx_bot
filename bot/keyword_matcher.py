import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class IntentMatch:
    intent: str
    params: dict
    confidence: str  # "keyword" | "llm" | "none"


# ─── PATTERNS ──────────────────────────────────────────────────────────────
# Cada entrada: (intent, [lista de patrones regex])
# Los patrones se prueban en orden; el primero que matchea gana.

_PATTERNS: list[tuple[str, list[str]]] = [
    ("mis_asignaciones", [
        r"\bqu[eé]\s+(tengo|me\s+toca|tengo\s+yo)\b",
        r"\bmis?\s+(archivos?|asignaciones?|tareas?|pendientes?)\b",
        r"\bqu[eé]\s+debo\s+(hacer|trabajar)\b",
        r"\btengo\s+(algo|trabajo)\s+pendiente\b",
        r"\bmi\s+lista\b",
        r"\bmio",
    ]),
    ("asignaciones_equipo", [
        r"\b(equipo|todos?)\b.*\b(tiene[n]?|asignaci[oó]n|estado|haciendo|trabajando)\b",
        r"\b(c[oó]mo|qu[eé])\s+(vamos|est[aá](n|mos))\b",
        r"\bestado\s+del\s+equipo\b",
        r"\bqu[eé]\s+(est[aá](n|mos)|tienen)\s+(haciendo|trabajando)\b",
    ]),
    ("buscar_archivo", [
        r"\bqui[eé]n\s+(tiene|est[aá]\s+en|trabaja)\b",
        r"\bestado\s+d(el?|e\s+la)\s+archivo\b",
        r"\barchivo\s+\w+",
        r"\bqui[eé]n\s+trabaja\b",
    ]),
    ("marcar_en_curso", [
        r"\b(empec[eé]|arranco|comienzo|voy\s+a\s+empezar|estoy\s+trabajando)\b.*\b(\d+)\b",
        r"\b(\d+)\b.*\b(en\s+curso|empec[eé]|arranco)\b",
    ]),
    ("marcar_listo", [
        r"\b(termin[eé]|listo|entregu[eé]|ya\s+est[aá]|hecho)\b.*\b(\d+)\b",
        r"\b(\d+)\b.*\b(termin[eé]|listo|entregu[eé])\b",
    ]),
    ("marcar_bloqueado", [
        r"\b(bloqueado|bloqueo|problema|no\s+puedo\s+avanzar|estoy\s+trabado)\b.*\b(\d+)\b",
        r"\b(\d+)\b.*\b(bloqueado|problema|trabado)\b",
    ]),
]


def _extract_id(text: str) -> Optional[int]:
    """Extract the first integer found in a string."""
    match = re.search(r"\b(\d+)\b", text)
    return int(match.group(1)) if match else None


def _extract_query(text: str) -> str:
    """Extract a file/asset search query by stripping common noise words."""
    noise = r"\b(qui[eé]n|tiene|est[aá]|en|el|la|archivo|del|de|trabaja|trabajando)\b"
    cleaned = re.sub(noise, " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


# ─── PUBLIC API ────────────────────────────────────────────────────────────

def keyword_match(text: str) -> Optional[IntentMatch]:
    """
    Try to match text against keyword patterns.
    Returns IntentMatch if confident, None if unsure (→ fall through to LLM).
    """
    text_lower = text.lower().strip()

    for intent, patterns in _PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                params = _build_params(intent, text_lower)
                return IntentMatch(intent=intent, params=params, confidence="keyword")

    return None  # no match → LLM fallback


def _build_params(intent: str, text: str) -> dict:
    if intent == "buscar_archivo":
        return {"query": _extract_query(text)}
    if intent in ("marcar_en_curso", "marcar_listo", "marcar_bloqueado"):
        aid = _extract_id(text)
        return {"assignment_id": aid} if aid else {}
    return {}
