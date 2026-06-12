"""
Bot de WhatsApp — neonize sync + bridge a código async.

Los handlers de neonize son sync (más estable), pero bot_core.api_client e
bot_core.intent_resolver son async (aiohttp). Levantamos un event loop en un
thread aparte y mandamos las corutinas ahí con run_coroutine_threadsafe.

Uso (desde la raíz del repo):
    python -m bot_wa.bot

Asegurate de haber corrido bot_wa.smoke_test al menos una vez para tener la
sesión de WhatsApp persistida en bot_wa/session/store.db.
"""

import asyncio
import logging
import os
import re
import threading
from pathlib import Path

from dotenv import load_dotenv
from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv

from bot_core.api_client import APIClient, APIError
from bot_core.intent_resolver import resolve_intent

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot_wa")

api = APIClient(base_url=os.getenv("API_BASE_URL", "http://localhost:8000"))
GROUP_TRIGGER = os.getenv("GROUP_TRIGGER", "bot").lower()

SESSION_DIR = Path(__file__).parent / "session"
SESSION_DIR.mkdir(exist_ok=True)
DB_PATH = SESSION_DIR / "store.db"

client = NewClient(str(DB_PATH))

STATUS_LABELS = {
    "pending":     "⏳ PENDIENTE",
    "in_progress": "🔶 EN CURSO",
    "done":        "✅ LISTO",
    "blocked":     "🔴 BLOQUEADO",
}


# ─── ASYNC BRIDGE ──────────────────────────────────────────────────────────
# Loop dedicado corriendo en un thread daemon. Los handlers sync de neonize
# mandan corutinas acá vía run_coroutine_threadsafe(...).result().

_async_loop = asyncio.new_event_loop()


def _start_async_loop():
    asyncio.set_event_loop(_async_loop)
    _async_loop.run_forever()


threading.Thread(target=_start_async_loop, daemon=True, name="bot-async-loop").start()


def run_async(coro):
    """Ejecuta una corutina en el loop de background y bloquea hasta el resultado."""
    return asyncio.run_coroutine_threadsafe(coro, _async_loop).result()


# ─── HELPERS ───────────────────────────────────────────────────────────────

def extract_text(message: MessageEv) -> str:
    msg = message.Message
    if msg.conversation:
        return msg.conversation
    if msg.extendedTextMessage and msg.extendedTextMessage.text:
        return msg.extendedTextMessage.text
    return ""


def is_for_bot(message: MessageEv, text: str) -> bool:
    if not message.Info.MessageSource.IsGroup:
        return True
    return GROUP_TRIGGER in text.lower()


def strip_trigger(text: str) -> str:
    return re.sub(rf"\b{re.escape(GROUP_TRIGGER)}\b", "", text, flags=re.IGNORECASE).strip()


def format_assignment(a: dict) -> str:
    asset   = a.get("asset", {})
    status  = STATUS_LABELS.get(a["status"], a["status"])
    version = f" `{asset['current_version']}`" if asset.get("current_version") else ""
    drive   = f"\n   ↗ {asset['drive_url']}" if asset.get("drive_url") else "\n   _sin link de Drive_"
    notes   = f"\n   📝 _{a['notes']}_" if a.get("notes") else ""
    return f"• *{asset.get('name', '?')}*{version} — {status}  id:`{a['id']}`{drive}{notes}"


def reply(c, message, text: str):
    c.send_message(message.Info.MessageSource.Chat, text)


# ─── INTENT HANDLERS ───────────────────────────────────────────────────────
# Son sync — usan run_async() para los llamados HTTP/LLM.

def handle_mis_asignaciones(c, message, person):
    data = run_async(api.get(f"/persons/{person['id']}/assignments"))
    assignments = data.get("assignments", [])
    if not assignments:
        reply(c, message, "✅ No tenés asignaciones activas.")
        return
    lines = [f"📋 *Tus asignaciones* ({len(assignments)}):\n"]
    lines += [format_assignment(a) for a in assignments]
    reply(c, message, "\n".join(lines))


def handle_asignaciones_equipo(c, message, person):
    team_id   = person.get("team", {}).get("id")
    team_name = person.get("team", {}).get("name", "Tu equipo")
    if not team_id:
        reply(c, message, "❌ No tenés equipo asignado.")
        return
    data        = run_async(api.get(f"/assignments/team/{team_id}"))
    assignments = data.get("assignments", [])
    if not assignments:
        reply(c, message, f"✅ *{team_name}* no tiene asignaciones activas.")
        return
    lines = [f"👥 *{team_name}* — {len(assignments)} asignaciones:\n"]
    for a in assignments:
        person_name = a.get("person", {}).get("name", "?")
        line = format_assignment(a)
        line = line.replace("• ", f"• {person_name} — ", 1)
        lines.append(line)
    reply(c, message, "\n".join(lines))


def handle_buscar_archivo(c, message, search_term):
    if not search_term:
        reply(c, message, "🔍 ¿Qué archivo buscás? Ejemplo: _comp escena 4_")
        return
    assets  = run_async(api.get("/assets"))
    matches = [a for a in assets if search_term.lower() in a["name"].lower()]
    if not matches:
        reply(c, message, f"🔍 No encontré ningún asset con *{search_term}*.")
        return
    lines = []
    for asset in matches[:5]:
        version = f" `{asset['current_version']}`" if asset.get("current_version") else ""
        drive   = f"\n   ↗ {asset['drive_url']}" if asset.get("drive_url") else "\n   _sin link de Drive_"
        lines.append(f"\n📁 *{asset['name']}*{version}{drive}")
        asset_assignments = run_async(api.get(f"/assets/{asset['id']}/assignments"))
        if asset_assignments:
            for a in asset_assignments:
                lines.append(f"  → {a.get('person', {}).get('name', '?')} — {STATUS_LABELS.get(a['status'], a['status'])}")
        else:
            lines.append("  → Sin asignaciones activas")
    reply(c, message, "\n".join(lines))


def handle_change_status(c, message, person, assignment_id, new_status, search_term):
    if not assignment_id and search_term:
        person_data = run_async(api.get(f"/persons/{person['id']}/assignments"))
        assignments = person_data.get("assignments", [])
        matches = [a for a in assignments
                   if search_term.lower() in a.get("asset", {}).get("name", "").lower()]
        if len(matches) == 1:
            assignment_id = matches[0]["id"]
        elif len(matches) > 1:
            names = "\n".join(f"• id `{a['id']}` — {a['asset']['name']}" for a in matches)
            reply(c, message, f"Encontré varios archivos, especificá el id:\n{names}")
            return
        else:
            reply(c, message, f"❌ No encontré ninguna asignación tuya con *{search_term}*.\nMandá _mio_ para ver tus IDs.")
            return

    if not assignment_id:
        reply(c, message, "❌ Indicá el ID o el nombre del archivo. Mandá _mio_ para ver tus asignaciones.")
        return

    result = run_async(api.patch(
        f"/assignments/{assignment_id}/status",
        {"status": new_status, "changed_by": person["name"], "note": "Actualizado por bot"},
    ))
    asset_name = result.get("asset", {}).get("name", f"#{assignment_id}")
    reply(c, message, f"{STATUS_LABELS[new_status]} *{asset_name}* actualizado.")


HELP_TEXT = (
    "🎬 *Asset Manager Bot — Guía rápida*\n\n"
    "Escribime en lenguaje natural, sin comandos.\n"
    f"En grupos, incluí la palabra *{GROUP_TRIGGER}* en tu mensaje.\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "📋 *CONSULTAR TUS ARCHIVOS*\n"
    "• _qué tengo asignado_\n"
    "• _mis archivos_\n\n"
    "👥 *VER TU EQUIPO*\n"
    "• _cómo está el equipo_\n"
    "• _asignaciones del equipo_\n\n"
    "🔍 *BUSCAR UN ARCHIVO*\n"
    "• _quién tiene el comp final_\n\n"
    "🔶 *AVISAR QUE EMPEZASTE*\n"
    "• _empecé con la escena 4_\n\n"
    "✅ *AVISAR QUE TERMINASTE*\n"
    "• _terminé la escena 4_\n\n"
    "🔴 *REPORTAR UN BLOQUEO*\n"
    "• _estoy bloqueado en la escena 4_\n"
)


def handle_ayuda(c, message):
    reply(c, message, HELP_TEXT)


# ─── MAIN MESSAGE ROUTER ───────────────────────────────────────────────────

@client.event(MessageEv)
def on_message(c, message: MessageEv):
    if message.Info.MessageSource.IsFromMe:
        return

    raw_text = extract_text(message)
    if not raw_text:
        return

    if not is_for_bot(message, raw_text):
        return

    text = strip_trigger(raw_text) if message.Info.MessageSource.IsGroup else raw_text
    if not text:
        reply(c, message, HELP_TEXT)
        return

    sender_number = message.Info.MessageSource.Sender.User

    try:
        person = run_async(api.get(f"/persons/by-whatsapp/{sender_number}"))
    except APIError as e:
        if e.status == 404:
            reply(
                c, message,
                f"⚠️ No estás registrado.\n"
                f"Pasale este número a tu admin: `{sender_number}`",
            )
        else:
            reply(c, message, f"❌ Error consultando registro: {e}")
        return

    resolved = run_async(resolve_intent(text))
    intent   = resolved["intent"]
    search   = resolved.get("search_term")
    asgn_id  = resolved.get("assignment_id")

    logger.info(
        f"[{sender_number}] '{text}' → {intent} "
        f"(via {resolved['method']}, confidence: {resolved.get('confidence')})"
    )

    try:
        if intent == "mis_asignaciones":
            handle_mis_asignaciones(c, message, person)
        elif intent == "asignaciones_equipo":
            handle_asignaciones_equipo(c, message, person)
        elif intent == "buscar_archivo":
            handle_buscar_archivo(c, message, search)
        elif intent == "marcar_en_curso":
            handle_change_status(c, message, person, asgn_id, "in_progress", search)
        elif intent == "marcar_listo":
            handle_change_status(c, message, person, asgn_id, "done", search)
        elif intent == "marcar_bloqueado":
            handle_change_status(c, message, person, asgn_id, "blocked", search)
        else:
            handle_ayuda(c, message)
    except APIError as e:
        reply(c, message, f"❌ Error al consultar la API: {e}")


# ─── LIFECYCLE ─────────────────────────────────────────────────────────────

@client.event(ConnectedEv)
def on_connected(_c, _ev):
    logger.info("✅ Bot conectado a WhatsApp. Esperando mensajes...")


@client.event(PairStatusEv)
def on_pair(_c, event):
    logger.info(f"📱 Pareado como: {event.ID.User}")


if __name__ == "__main__":
    client.connect()
