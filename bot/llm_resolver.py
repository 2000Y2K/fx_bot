import json
import os
import aiohttp
import logging
from keyword_matcher import IntentMatch
from intents import INTENTS

logger = logging.getLogger(__name__)

# Configurable via .env — works with OpenAI, Claude (via proxy), Groq, etc.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "gpt-4o-mini")


_SYSTEM_PROMPT = """Sos el asistente de un sistema de gestión de assets audiovisuales.
Tu tarea es analizar mensajes de trabajadores y determinar su intención.

Intenciones posibles:
{intent_list}

Respondé ÚNICAMENTE con un JSON con este formato exacto, sin texto extra:
{{"intent": "nombre_del_intent", "params": {{"param1": "valor1"}}}}

Si hay un número en el mensaje que parece ser un ID de asignación, incluilo en params como "assignment_id" (número entero).
Si hay un nombre de archivo o búsqueda, incluilo como "query" (string).
Si no podés determinar la intención, usá "desconocido" con params vacío {{}}.
"""

def _build_system_prompt() -> str:
    lines = []
    for name, info in INTENTS.items():
        if name == "desconocido":
            continue
        examples = ", ".join(f'"{e}"' for e in info["examples"][:2])
        lines.append(f'- "{name}": {info["description"]}. Ejemplos: {examples}')
    return _SYSTEM_PROMPT.format(intent_list="\n".join(lines))


async def llm_resolve(text: str) -> IntentMatch:
    """
    Call an OpenAI-compatible API to classify intent.
    Falls back to 'desconocido' on any error.
    """
    if not LLM_API_KEY:
        logger.warning("LLM_API_KEY not set, skipping LLM resolution")
        return IntentMatch(intent="desconocido", params={}, confidence="none")

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user",   "content": text},
        ],
        "temperature": 0,
        "max_tokens": 150,
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LLM_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(f"LLM API error {resp.status}: {body}")
                    return IntentMatch(intent="desconocido", params={}, confidence="none")

                data = await resp.json()
                raw  = data["choices"][0]["message"]["content"].strip()

                # Strip markdown code fences if present
                raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

                parsed = json.loads(raw)
                intent = parsed.get("intent", "desconocido")
                params = parsed.get("params", {})

                # Normalize assignment_id to int if present
                if "assignment_id" in params and params["assignment_id"] is not None:
                    try:
                        params["assignment_id"] = int(params["assignment_id"])
                    except (ValueError, TypeError):
                        params.pop("assignment_id")

                logger.info(f"LLM resolved '{text}' → {intent} {params}")
                return IntentMatch(intent=intent, params=params, confidence="llm")

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"LLM response parse error: {e}")
        return IntentMatch(intent="desconocido", params={}, confidence="none")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return IntentMatch(intent="desconocido", params={}, confidence="none")
