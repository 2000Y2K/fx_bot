import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from api_client import APIClient, APIError
from intent_resolver import resolve_intent

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

api = APIClient(base_url=os.getenv("API_BASE_URL", "http://localhost:8000"))

STATUS_LABELS = {
    "pending":     "⏳ PENDIENTE",
    "in_progress": "🔶 EN CURSO",
    "done":        "✅ LISTO",
    "blocked":     "🔴 BLOQUEADO",
}


# ─── HELPERS ───────────────────────────────────────────────────────────────

async def get_person(telegram_id: int):
    return await api.get(f"/persons/by-telegram/{telegram_id}")


def format_assignment(a: dict) -> str:
    asset   = a.get("asset", {})
    status  = STATUS_LABELS.get(a["status"], a["status"])
    version = f" <code>{asset['current_version']}</code>" if asset.get("current_version") else ""
    drive   = f"\n   ↗ <a href=\"{asset['drive_url']}\">Ver archivo</a>" if asset.get("drive_url") else "\n   <i>sin link de Drive</i>"
    notes   = f"\n   📝 <i>{a['notes']}</i>" if a.get("notes") else ""
    return f"• <b>{asset.get('name', '?')}</b>{version} — {status}  ID:<code>{a['id']}</code>{drive}{notes}"


async def reply(update: Update, text: str, **kwargs):
    await update.message.reply_text(text, parse_mode="HTML",
                                    disable_web_page_preview=False, **kwargs)


# ─── INTENT HANDLERS ───────────────────────────────────────────────────────

async def handle_mis_asignaciones(update: Update, person: dict):
    data = await api.get(f"/persons/{person['id']}/assignments")
    assignments = data.get("assignments", [])
    if not assignments:
        await reply(update, "✅ No tenés asignaciones activas.")
        return
    lines = [f"📋 <b>Tus asignaciones</b> ({len(assignments)}):\n"]
    lines += [format_assignment(a) for a in assignments]
    await reply(update, "\n".join(lines))


async def handle_asignaciones_equipo(update: Update, person: dict):
    team_id   = person.get("team", {}).get("id")
    team_name = person.get("team", {}).get("name", "Tu equipo")
    if not team_id:
        await reply(update, "❌ No tenés equipo asignado.")
        return
    data        = await api.get(f"/assignments/team/{team_id}")
    assignments = data.get("assignments", [])
    if not assignments:
        await reply(update, f"✅ <b>{team_name}</b> no tiene asignaciones activas.")
        return
    lines = [f"👥 <b>{team_name}</b> — {len(assignments)} asignaciones:\n"]
    for a in assignments:
        person_name = a.get("person", {}).get("name", "?")
        line = format_assignment(a)
        line = line.replace("• ", f"• {person_name} — ", 1)
        lines.append(line)
    await reply(update, "\n".join(lines))


async def handle_buscar_archivo(update: Update, search_term: str):
    if not search_term:
        await reply(update, "🔍 ¿Qué archivo buscás? Ejemplo: <i>comp escena 4</i>")
        return
    assets  = await api.get("/assets")
    matches = [a for a in assets if search_term.lower() in a["name"].lower()]
    if not matches:
        await reply(update, f"🔍 No encontré ningún asset con <b>{search_term}</b>.")
        return
    lines = []
    for asset in matches[:5]:
        version = f" <code>{asset['current_version']}</code>" if asset.get("current_version") else ""
        drive   = f"\n   ↗ <a href=\"{asset['drive_url']}\">Ver archivo</a>" if asset.get("drive_url") else "\n   <i>sin link de Drive</i>"
        lines.append(f"\n📁 <b>{asset['name']}</b>{version}{drive}")
        asset_assignments = await api.get(f"/assets/{asset['id']}/assignments")
        if asset_assignments:
            for a in asset_assignments:
                lines.append(f"  → {a.get('person', {}).get('name', '?')} — {STATUS_LABELS.get(a['status'], a['status'])}")
        else:
            lines.append("  → Sin asignaciones activas")
    await reply(update, "\n".join(lines))


async def handle_change_status(update: Update, person: dict, assignment_id: int | None,
                                new_status: str, search_term: str | None):
    if not assignment_id and search_term:
        person_data = await api.get(f"/persons/{person['id']}/assignments")
        assignments = person_data.get("assignments", [])
        matches = [a for a in assignments
                   if search_term.lower() in a.get("asset", {}).get("name", "").lower()]
        if len(matches) == 1:
            assignment_id = matches[0]["id"]
        elif len(matches) > 1:
            names = "\n".join(f"• ID <code>{a['id']}</code> — {a['asset']['name']}" for a in matches)
            await reply(update, f"Encontré varios archivos, especificá el ID:\n{names}")
            return
        else:
            await reply(update, f"❌ No encontré ninguna asignación tuya con <b>{search_term}</b>.\nUsá /mio para ver tus IDs.")
            return

    if not assignment_id:
        await reply(update, "❌ Indicá el ID o el nombre del archivo. Usá /mio para ver tus asignaciones.")
        return

    result     = await api.patch(f"/assignments/{assignment_id}/status",
                                 {"status": new_status, "changed_by": person["name"],
                                  "note": "Actualizado por bot"})
    asset_name = result.get("asset", {}).get("name", f"#{assignment_id}")
    await reply(update, f"{STATUS_LABELS[new_status]} <b>{asset_name}</b> actualizado.")


HELP_TEXT = (
    "🎬 <b>Asset Manager Bot — Guía rápida</b>\n\n"
    "Escribime en lenguaje natural, sin comandos especiales.\n"
    "En grupos, etiquetame primero: <code>@bot tu mensaje</code>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "📋 <b>CONSULTAR TUS ARCHIVOS</b>\n"
    "• <i>qué tengo asignado</i>\n"
    "• <i>qué me toca hacer</i>\n"
    "• <i>mis archivos</i>\n\n"
    "👥 <b>VER TU EQUIPO</b>\n"
    "• <i>cómo está el equipo</i>\n"
    "• <i>qué están haciendo todos</i>\n"
    "• <i>asignaciones del equipo</i>\n\n"
    "🔍 <b>BUSCAR UN ARCHIVO</b>\n"
    "• <i>quién tiene el comp final</i>\n"
    "• <i>cómo está la escena 4</i>\n"
    "• <i>busco el modelo del personaje</i>\n\n"
    "🔶 <b>AVISAR QUE EMPEZASTE</b>\n"
    "• <i>empecé con la escena 4</i>\n"
    "• <i>arranqué el comp final</i>\n"
    "• <i>estoy trabajando en el audio</i>\n\n"
    "✅ <b>AVISAR QUE TERMINASTE</b>\n"
    "• <i>terminé la escena 4</i>\n"
    "• <i>listo el comp final</i>\n"
    "• <i>entregué el modelo</i>\n\n"
    "🔴 <b>REPORTAR UN BLOQUEO</b>\n"
    "• <i>estoy bloqueado en la escena 4</i>\n"
    "• <i>no puedo avanzar con el audio</i>\n"
    "• <i>tengo un problema con el comp</i>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "💡 <b>TIPS</b>\n"
    "• Si mencionás un nombre de archivo, lo busco en tus asignaciones automáticamente.\n"
    "• Si tenés varias asignaciones con nombres similares, te pido que confirmes cuál.\n"
    "• Usá /start para ver tu Telegram ID (necesario para que el admin te registre).\n"
)

async def handle_ayuda(update: Update):
    await reply(update, HELP_TEXT)


# ─── MAIN MESSAGE ROUTER ───────────────────────────────────────────────────

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text         = update.message.text
    chat         = update.message.chat
    bot_username = ctx.bot.username

    if chat.type in ("group", "supergroup"):
        is_mention      = f"@{bot_username}".lower() in text.lower()
        is_reply_to_bot = (
            update.message.reply_to_message is not None and
            update.message.reply_to_message.from_user is not None and
            update.message.reply_to_message.from_user.id == ctx.bot.id
        )
        if not is_mention and not is_reply_to_bot:
            return

    try:
        person = await get_person(update.effective_user.id)
    except APIError:
        await reply(update, "❌ No estás registrado. Pedile a tu admin que te agregue con tu Telegram ID.")
        return

    resolved = await resolve_intent(text)
    intent   = resolved["intent"]
    search   = resolved.get("search_term")
    asgn_id  = resolved.get("assignment_id")

    logger.info(
        f"[{update.effective_user.username}] '{text}' "
        f"→ {intent} (via {resolved['method']}, confidence: {resolved['confidence']})"
    )

    try:
        if intent == "mis_asignaciones":
            await handle_mis_asignaciones(update, person)
        elif intent == "asignaciones_equipo":
            await handle_asignaciones_equipo(update, person)
        elif intent == "buscar_archivo":
            await handle_buscar_archivo(update, search)
        elif intent == "marcar_en_curso":
            await handle_change_status(update, person, asgn_id, "in_progress", search)
        elif intent == "marcar_listo":
            await handle_change_status(update, person, asgn_id, "done", search)
        elif intent == "marcar_bloqueado":
            await handle_change_status(update, person, asgn_id, "blocked", search)
        else:
            await handle_ayuda(update)
    except APIError as e:
        await reply(update, f"❌ Error al consultar la API: {e}")


# ─── COMMANDS ──────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_user.id
    name    = update.effective_user.first_name
    # Check if already registered
    try:
        person = await get_person(chat_id)
        registered_msg = f"✅ Ya estás registrado como <b>{person['name']}</b> en el equipo <b>{person['team']['name']}</b>.\n\n"
    except APIError:
        registered_msg = (
            f"⚠️ Todavía no estás registrado en el sistema.\n"
            f"Pasale este ID a tu admin: <code>{chat_id}</code>\n\n"
        )
    await update.message.reply_text(
        f"👋 Hola <b>{name}</b>!\n\n"
        f"{registered_msg}"
        f"Mandame <b>/help</b> para ver todo lo que puedo hacer.",
        parse_mode="HTML",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


async def cmd_mio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        person = await get_person(update.effective_user.id)
        await handle_mis_asignaciones(update, person)
    except APIError:
        await reply(update, "❌ No estás registrado en el sistema.")


async def cmd_equipo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        person = await get_person(update.effective_user.id)
        await handle_asignaciones_equipo(update, person)
    except APIError:
        await reply(update, "❌ No estás registrado en el sistema.")


# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Falta TELEGRAM_BOT_TOKEN en el .env")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("mio",    cmd_mio))
    app.add_handler(CommandHandler("equipo", cmd_equipo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot iniciado con NLP (keywords + LLM fallback). Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()