"""
Intent resolver — keywords first, LLM fallback.
Agnostic to LLM provider: works with OpenAI, Anthropic, or any OpenAI-compatible API.
"""

import os
import re
import json
import logging
import aiohttp

logger = logging.getLogger(__name__)

# ─── INTENT DEFINITIONS ────────────────────────────────────────────────────
# Used both for keyword matching AND as context sent to the LLM.

INTENTS = {
    "mis_asignaciones": {
        "description": "El usuario quiere saber qué archivos o tareas tiene asignados.",
        "examples": ["qué tengo", "mis archivos", "qué me toca", "tengo algo asignado", "mis tareas", "qué debo hacer"],
        "keywords": [r"\bmi[os]?\b.*\b(asignaci[oó]n|archivo|tarea|trabajo)\b",
                     r"\bqu[eé]\s+(tengo|me\s+toca|debo)\b",
                     r"\btengo\s+algo\b",
                     r"\bmi[os]?\s+(archivos?|tareas?)\b"],
    },
    "asignaciones_equipo": {
        "description": "El usuario quiere ver las asignaciones de su equipo.",
        "examples": ["qué tiene el equipo", "cómo está el equipo", "asignaciones del equipo", "qué están haciendo"],
        "keywords": [r"\bequipo\b",
                     r"\bqu[eé]\s+tiene[n]?\b",
                     r"\bcompa[sñ]\b",
                     r"\btodos\b.*\b(hacen|trabajan|tienen)\b"],
    },
    "buscar_archivo": {
        "description": "El usuario quiere saber quién está trabajando en un archivo específico o buscar un asset por nombre.",
        "examples": ["quién tiene la escena 4", "cómo está el comp final", "busco el archivo de audio", "cómo está render.mp4"],
        "keywords": [r"\bqui[eé]n\s+(tiene|trabaja|est[aá])\b",
                     r"\bc[oó]mo\s+est[aá]\b.*\barchivo\b",
                     r"\bbusco?\b",
                     r"\bestado\s+de[l]?\b",
                     r"\b\w[\w\-]*\.\w{2,5}\b"],  # nombre.ext directamente
        "requires_arg": True,
    },
    "marcar_en_curso": {
        "description": "El usuario avisa que empezó a trabajar en algo.",
        "examples": ["empecé con la escena 4", "arranqué el comp", "estoy trabajando en el modelo"],
        "keywords": [r"\bempec[eé]\b",
                     r"\barranqu[eé]\b",
                     r"\bestoy\s+trabajando\b",
                     r"\bme\s+puse\b",
                     r"\btomé?\b.*\barchivo\b"],
        "requires_arg": True,
    },
    "marcar_listo": {
        "description": "El usuario avisa que terminó una tarea o archivo.",
        "examples": ["terminé la escena 4", "listo el comp", "ya entregué el modelo", "finalisé"],
        "keywords": [r"\btermin[eé]\b",
        	         r"\blisto\b",
                     r"\bentregu[eé]\b",
                     r"\bya\s+(hice|termin[eé]|entregu[eé])\b",
                     r"\bfinalic[eé]\b"],
        "requires_arg": True,
    },
    "marcar_bloqueado": {
        "description": "El usuario reporta que está bloqueado, tiene un problema o no puede avanzar.",
        "examples": ["estoy bloqueado en la escena 4", "no puedo avanzar", "tengo un problema con el audio"],
        "keywords": [r"\bbloqueado\b",
                     r"\bno\s+puedo\s+avanzar\b",
                     r"\btengo\s+un\s+problema\b",
                     r"\bstuck\b",
                     r"\btraba[dr]\b"],
        "requires_arg": True,
    },
    "ayuda": {
        "description": "El usuario pide ayuda o no sabe qué puede hacer.",
        "examples": ["ayuda", "qué puedo hacer", "cómo funciona", "comandos"],
        "keywords": [r"\bayuda\b", r"\bhelp\b", r"\bcomandos?\b", r"\bqu[eé]\s+puedo\b", r"\bc[oó]mo\s+funciona\b"],
    },
}

# ─── KEYWORD MATCHING ──────────────────────────────────────────────────────

def match_keywords(text: str) -> str | None:
    """Try to match text to an intent using regex keywords. Returns intent name or None."""
    text_lower = text.lower()
    for intent_name, intent in INTENTS.items():
        for pattern in intent["keywords"]:
            if re.search(pattern, text_lower):
                logger.debug(f"Keyword match: '{text}' → {intent_name} (pattern: {pattern})")
                return intent_name
    return None


# Intent verbs to strip before extracting the asset name
_INTENT_VERBS = (
    r"\bempec[eé]\b", r"\barranqu[eé]\b", r"\bme\s+puse\b", r"\bestoy\s+trabajando\s+(en|con)?\b",
    r"\btermin[eé]\b", r"\bentregu[eé]\b", r"\bfinalic[eé]\b", r"\bya\s+(hice|termin[eé]|entregu[eé])\b",
    r"\bestoy\s+bloqueado\s*(en|con)?\b", r"\btengo\s+un\s+problema\s*(con)?\b", r"\bno\s+puedo\s+avanzar\s*(con|en)?\b",
    r"\blisto\b", r"\bhecho\b", r"\btomé?\b",
)

_STOPWORDS = (
    r"\b(el|la|los|las|un|una|del|al|de|en|con|que|qué|cómo|está|tengo|tiene|mi|mis|archivo|tarea)\b"
)

# Bot @mention
_MENTION = r"@\w+"


def extract_search_term(text: str) -> str:
    """
    Strip intent verbs, bot mention, stopwords and return the remaining
    token(s) — which should be the asset name the user referred to.
    Prioritizes nombre.ext patterns since assets always use that format.
    """
    # Primero intentar extraer un nombre.ext directamente
    filename_match = re.search(r"\b(\w[\w\-]*\.\w{2,5})\b", text, re.IGNORECASE)
    if filename_match:
        return filename_match.group(1).lower()

    clean = text.lower()
    clean = re.sub(_MENTION, "", clean)
    for verb_pat in _INTENT_VERBS:
        clean = re.sub(verb_pat, "", clean)
    clean = re.sub(_STOPWORDS, "", clean)
    clean = re.sub(r"[^\w\s_\-.]", " ", clean)   # keep chars common in filenames
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean if len(clean) > 1 else text.strip()


# ─── LLM FALLBACK ──────────────────────────────────────────────────────────

INTENTS_CONTEXT = "\n".join(
    f"- {name}: {data['description']} (ejemplos: {', '.join(data['examples'][:3])})"
    for name, data in INTENTS.items()
)

SYSTEM_PROMPT = f"""Sos un clasificador de intenciones para un bot de gestión de assets en producción audiovisual.
Tu única tarea es clasificar el mensaje del usuario en UNA de estas intenciones:

{INTENTS_CONTEXT}

IMPORTANTE: Los assets siempre tienen el formato nombre.extensión (ej: render.mp4, audio.wav, escena4.blend, comp_final.aep).
Si el usuario menciona una palabra con ese formato, es casi seguro que se refiere a un asset.

Respondé ÚNICAMENTE con un JSON con este formato exacto, sin texto adicional:
{{
  "intent": "nombre_de_la_intencion",
  "search_term": "el nombre del asset con su extensión si aplica (ej: render.mp4), o null",
  "assignment_id": número si el usuario menciona un ID, o null,
  "confidence": "high" | "medium" | "low"
}}

Si el mensaje no corresponde a ninguna intención clara, usá intent: "ayuda".
"""


async def resolve_with_llm(text: str) -> dict:
    """
    Call the configured LLM provider to classify intent.
    Supports OpenAI-compatible APIs (OpenAI, Azure, local models via LM Studio, etc.)
    and Anthropic's API.
    """
    provider  = os.getenv("LLM_PROVIDER", "openai").lower()  # "openai" | "anthropic"
    api_key   = os.getenv("LLM_API_KEY", "")
    model     = os.getenv("LLM_MODEL", "gpt-4o-mini")
    base_url  = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        logger.warning("LLM_API_KEY not set, skipping LLM resolution")
        return {"intent": "ayuda", "search_term": None, "assignment_id": None, "confidence": "low"}

    try:
        if provider == "anthropic":
            return await _call_anthropic(text, api_key, model)
        else:
            return await _call_openai_compatible(text, api_key, model, base_url)
    except Exception as e:
        logger.error(f"LLM resolution failed: {e}")
        return {"intent": "ayuda", "search_term": None, "assignment_id": None, "confidence": "low"}


async def _call_openai_compatible(text: str, api_key: str, model: str, base_url: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": text},
        ],
        "temperature": 0,
        "max_tokens": 150,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/chat/completions", headers=headers, json=payload) as r:
            r.raise_for_status()
            data = await r.json()
            raw = data["choices"][0]["message"]["content"].strip()
            return _parse_llm_response(raw)


async def _call_anthropic(text: str, api_key: str, model: str) -> dict:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "claude-haiku-4-5-20251001",
        "max_tokens": 150,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": text}],
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload) as r:
            r.raise_for_status()
            data = await r.json()
            raw = data["content"][0]["text"].strip()
            return _parse_llm_response(raw)


def _parse_llm_response(raw: str) -> dict:
    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(clean)
        # Validate intent exists
        if result.get("intent") not in INTENTS:
            result["intent"] = "ayuda"
        return result
    except Exception:
        logger.warning(f"Could not parse LLM response: {raw}")
        return {"intent": "ayuda", "search_term": None, "assignment_id": None, "confidence": "low"}


# ─── MAIN RESOLVER ─────────────────────────────────────────────────────────

async def resolve_intent(text: str) -> dict:
    """
    Main entry point.
    1. Try keyword matching (fast, free).
    2. If no match, call LLM with full intent context.
    Returns dict with: intent, search_term, assignment_id, confidence, method
    """
    # Strip bot mention if present (@botname)
    clean_text = re.sub(r"@\w+", "", text).strip()

    # 1 — keyword match
    intent = match_keywords(clean_text)
    if intent:
        return {
            "intent": intent,
            "search_term": extract_search_term(clean_text),
            "assignment_id": _extract_id(clean_text),
            "confidence": "high",
            "method": "keyword",
        }

    # 2 — LLM fallback
    logger.info(f"No keyword match for '{clean_text}', trying LLM...")
    result = await resolve_with_llm(clean_text)
    result["method"] = "llm"
    if not result.get("search_term"):
        result["search_term"] = extract_search_term(clean_text)
    return result


def _extract_id(text: str) -> int | None:
    """Extract a numeric ID from text if present."""
    match = re.search(r'\b(\d+)\b', text)
    return int(match.group(1)) if match else None