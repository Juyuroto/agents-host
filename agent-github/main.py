import logging
import os
import time
from datetime import datetime

import requests

import historique
import suivis
from classifier import diagnose_repo
from config import DISCORD_OWNER_ID
from discord_inbox import fetch_messages, latest_message_id, new_requests
from github_client import analyze_repo_data, list_repos
from notifier import notify_discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-github")

POLL_SECONDS = 10
REPORT_HOUR, REPORT_MINUTE = 9, 30


def format_section(name: str, diag: dict, alertes: list[str], changes: list[str]) -> str:
    lines = [f"**{name}**", f"Statut : {diag['statut']}"]
    for a in alertes:
        lines.append(f":warning: {a}")
    for c in changes:
        lines.append(f"+ {c}")
    for obs in diag["observations"]:
        lines.append(f"- {obs}")
    for s in diag["suggestions"]:
        lines.append(f"> {s['action']} — {s['justification']}")
    return "\n".join(lines)


def run() -> None:
    day = datetime.now().strftime("%Y-%m-%d")
    names = suivis.load()
    if not names:
        return
    repos = [r for r in list_repos() if r["full_name"] in names]
    prev = historique.previous(day)

    sections = []
    snapshot = {}
    for repo in repos:
        name = repo.get("full_name", "?")
        try:
            log.info("Analyse de %s", name)
            data = analyze_repo_data(repo)
            snapshot[name] = data.pop("snapshot")
            changes = historique.diff(prev[name], snapshot[name]) if prev and name in prev else []
            data["changements"] = changes
            diag = diagnose_repo(data)
            if diag["statut"] == "À jour" and not diag["suggestions"] and not data["alertes"] and not changes:
                continue
            sections.append(format_section(name, diag, data["alertes"], changes))
        except Exception:
            log.exception("Erreur sur %s", name)
            sections.append(f"Erreur sur {name}")

    historique.save(day, snapshot)
    header = f"**Rapport quotidien des dépôts suivis** — {len(repos)} dépôt(s) analysé(s)"
    if prev is None:
        header += "\nPremier passage : pas de comparaison avec un instantané précédent."
    notify_discord(header + "\n\n" + "\n\n".join(sections))


def handle_messages(messages: list[dict]) -> None:
    for message in new_requests(messages, DISCORD_OWNER_ID):
        command = suivis.parse_command(message["content"])
        if command:
            notify_discord(suivis.execute(*command, list_repos))


def main() -> None:
    last_id = None
    inbox_ok = True
    last_report = datetime.now().date() if os.path.exists(historique.path(datetime.now().strftime("%Y-%m-%d"))) else None
    started = False
    while True:
        try:
            if not started:
                last_id = latest_message_id()
                started = True
                log.info("En écoute sur le salon")
            messages = fetch_messages(last_id)
            handle_messages(messages)
            if messages:
                last_id = max((m["id"] for m in messages), key=int)
            inbox_ok = True
        except Exception as e:
            log.exception("Échec de la lecture du salon ou d'une commande")
            if inbox_ok:
                notify_discord(f"Erreur agent-github (salon ou commande) : {type(e).__name__}")
            inbox_ok = False

        now = datetime.now()
        if last_report != now.date() and (now.hour, now.minute) >= (REPORT_HOUR, REPORT_MINUTE):
            last_report = now.date()
            try:
                run()
            except requests.RequestException as e:
                log.exception("Impossible de lister les dépôts GitHub")
                notify_discord(f"Erreur agent-github (rapport quotidien) : {type(e).__name__}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
