import asyncio
import logging
from datetime import datetime, timedelta, timezone

import apple_calendar
import storage
from config import DISCORD_ASSISTANT_CHANNEL_ID, TIMEZONE

log = logging.getLogger("agent-assistant")

RESUME_HEURE = 8


def _resume_du_jour(maintenant: datetime) -> str:
    debut = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    fin = debut + timedelta(days=1)
    lignes = [f"**Résumé du {maintenant:%d/%m}**", "**Rappels**"]
    rappels = [
        r for r in storage.list_pending_reminders()
        if datetime.fromisoformat(r["echeance"]).astimezone(TIMEZONE).date() == maintenant.date()
    ]
    lignes += [
        f"- {datetime.fromisoformat(r['echeance']).astimezone(TIMEZONE):%H:%M} {r['texte']}" for r in rappels
    ] or ["- Aucun"]
    lignes.append("**Agenda**")
    try:
        evenements = apple_calendar.list_events(debut.isoformat(), fin.isoformat())
        lignes += [f"- {datetime.fromisoformat(e['debut']):%H:%M} {e['texte']}" for e in evenements] or ["- Rien de prévu"]
    except Exception:
        log.exception("Agenda Apple indisponible pour le résumé")
        lignes.append("- Indisponible")
    return "\n".join(lignes)


async def run_scheduler(client) -> None:
    await client.wait_until_ready()
    while True:
        try:
            maintenant = datetime.now(TIMEZONE)
            now = maintenant.astimezone(timezone.utc).isoformat(timespec="seconds")
            channel = client.get_channel(DISCORD_ASSISTANT_CHANNEL_ID)
            for rappel in storage.due_reminders(now):
                try:
                    await channel.send(f"Rappel #{rappel['id']} : {rappel['texte']} (écris « fait {rappel['id']} » une fois fait)")
                    storage.mark_sent(rappel["id"], now)
                except Exception:
                    log.exception("Échec de l'envoi du rappel %s", rappel["id"])
            aujourdhui = maintenant.date().isoformat()
            if maintenant.hour >= RESUME_HEURE and storage.get_meta("resume") != aujourdhui:
                await channel.send(_resume_du_jour(maintenant)[:2000])
                storage.set_meta("resume", aujourdhui)
        except Exception:
            log.exception("Erreur dans le planificateur")
        await asyncio.sleep(60)
