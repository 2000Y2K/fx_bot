import logging
from api_client import APIClient, APIError
from keyword_matcher import IntentMatch

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "pending":     "⏳ Pendiente",
    "in_progress": "🔶 En curso",
    "done":        "✅ Listo",
    "blocked":     "🔴 Bloqueado",
}


class IntentDispatcher:
    def __init__(self, api: APIClient):
        self.api = api

    async def dispatch(self, match: IntentMatch, person: dict) -> str:
        intent = match.intent
        params = match.params

        handlers = {
            "mis_asignaciones":    self._mis_asignaciones,
            "asignaciones_equipo": self._asignaciones_equipo,
            "buscar_archivo":      self._buscar_archivo,
            "marcar_en_curso":     self._marcar_en_curso,
            "marcar_listo":        self._marcar_listo,
            "marcar_bloqueado":    self._marcar_bloqueado,
            "desconocido":         self._desconocido,
        }

        handler = handlers.get(intent, self._desconocido)
        try:
            return await handler(params, person)
        except APIError as e:
            logger.error(f"APIError in dispatch({intent}): {e}")
            return f"❌ Error al consultar el sistema ({e.status}). Intentá de nuevo."
        except Exception as e:
            logger.error(f"Unexpected error in dispatch({intent}): {e}")
            return "❌ Algo salió mal. Avisale al admin."

    # ── HANDLERS ─────────────────────────────────────────────────────────

    async def _mis_asignaciones(self, params: dict, person: dict) -> str:
        data = await self.api.get(f"/persons/{person['id']}/assignments")
        assignments = data.get("assignments", [])

        if not assignments:
            return "✅ No tenés asignaciones activas por ahora."

        lines = [f"📋 *Tus asignaciones* ({len(assignments)}):"]
        for a in assignments:
            asset   = a.get("asset", {})
            status  = STATUS_LABELS.get(a["status"], a["status"])
            version = f" `{asset['current_version']}`" if asset.get("current_version") else ""
            drive   = f" — [Drive]({asset['drive_url']})" if asset.get("drive_url") else ""
            notes   = f"\n   📝 _{a['notes']}_" if a.get("notes") else ""
            lines.append(f"• *{asset.get('name', '?')}*{version} — {status}{drive}  `id:{a['id']}`{notes}")

        lines.append("\n_Para actualizar estado: mencioname con 'empecé el 3', 'terminé el 5', etc._")
        return "\n".join(lines)

    async def _asignaciones_equipo(self, params: dict, person: dict) -> str:
        team_id   = person.get("team", {}).get("id")
        team_name = person.get("team", {}).get("name", "tu equipo")

        if not team_id:
            return "❌ No tenés equipo asignado."

        data        = await self.api.get(f"/assignments/team/{team_id}")
        assignments = data.get("assignments", [])

        if not assignments:
            return f"✅ El equipo *{team_name}* no tiene asignaciones activas."

        lines = [f"👥 *{team_name}* — {len(assignments)} asignaciones:"]
        for a in assignments:
            asset       = a.get("asset", {})
            person_name = a.get("person", {}).get("name", "?")
            status      = STATUS_LABELS.get(a["status"], a["status"])
            version     = f" `{asset.get('current_version')}`" if asset.get("current_version") else ""
            lines.append(f"• *{asset.get('name', '?')}*{version} — {person_name} — {status}")

        return "\n".join(lines)

    async def _buscar_archivo(self, params: dict, person: dict) -> str:
        query = params.get("query", "").strip()
        if not query:
            return "¿Qué archivo querés buscar? Ej: _mencioname con 'quién tiene escena_04'_"

        assets = await self.api.get("/assets")
        matches = [a for a in assets if query.lower() in a["name"].lower()]

        if not matches:
            return f"🔍 No encontré ningún asset con *{query}*."

        lines = []
        for asset in matches[:4]:
            version = f" `{asset['current_version']}`" if asset.get("current_version") else ""
            drive   = f" — [Drive]({asset['drive_url']})" if asset.get("drive_url") else ""
            lines.append(f"\n📁 *{asset['name']}*{version}{drive}")

            asset_assignments = await self.api.get(f"/assets/{asset['id']}/assignments")
            if asset_assignments:
                for a in asset_assignments:
                    pname  = a.get("person", {}).get("name", "?")
                    status = STATUS_LABELS.get(a["status"], a["status"])
                    lines.append(f"  → {pname} — {status}")
            else:
                lines.append("  → Sin asignaciones activas")

        return "\n".join(lines)

    async def _change_status(self, params: dict, person: dict, new_status: str, verb: str) -> str:
        aid = params.get("assignment_id")
        if not aid:
            return f"¿Cuál es el ID de la asignación? Ej: _{verb} el 3_"

        result = await self.api.patch(
            f"/assignments/{aid}/status",
            {"status": new_status, "changed_by": person["name"], "note": f"Actualizado via bot"},
        )
        asset_name   = result.get("asset", {}).get("name", f"#{aid}")
        status_label = STATUS_LABELS.get(new_status, new_status)
        return f"{status_label} *{asset_name}* actualizado."

    async def _marcar_en_curso(self, params: dict, person: dict) -> str:
        return await self._change_status(params, person, "in_progress", "empecé el")

    async def _marcar_listo(self, params: dict, person: dict) -> str:
        return await self._change_status(params, person, "done", "terminé el")

    async def _marcar_bloqueado(self, params: dict, person: dict) -> str:
        return await self._change_status(params, person, "blocked", "bloqueado en el")

    async def _desconocido(self, params: dict, person: dict) -> str:
        return (
            "No entendí bien. Podés decirme cosas como:\n"
            "• _qué tengo yo_ — tus asignaciones\n"
            "• _cómo va el equipo_ — estado del equipo\n"
            "• _quién tiene escena\\_04_ — buscar un archivo\n"
            "• _empecé el 3_ / _terminé el 5_ / _bloqueado en el 2_ — actualizar estado"
        )
