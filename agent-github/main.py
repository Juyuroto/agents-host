import logging
import requests

from github_client import list_repos, analyze_repo_data
from classifier import diagnose_repo
from notifier import notify_discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-github")


def format_section(name: str, diag: dict) -> str:
    lines = [f"**{name}**", f"Statut : {diag['statut']}"]
    for obs in diag["observations"]:
        lines.append(f"- {obs}")
    for s in diag["suggestions"]:
        lines.append(f"> {s['action']} — {s['justification']}")
    return "\n".join(lines)


def run() -> None:
    try:
        repos = list_repos()
    except requests.RequestException:
        log.exception("Impossible de lister les dépôts GitHub")
        raise SystemExit(1)

    sections = []
    for repo in repos:
        name = repo.get("full_name", "?")
        try:
            log.info("Analyse de %s", name)
            data = analyze_repo_data(repo)
            diag = diagnose_repo(data)
            if diag["statut"] == "À jour" and not diag["suggestions"]:
                continue
            sections.append(format_section(name, diag))
        except Exception:
            log.exception("Erreur sur %s", name)
            sections.append(f"Erreur sur {name}")

    header = f"**Rapport hebdo des dépôts GitHub** — {len(repos)} dépôt(s) analysé(s)"
    notify_discord(header + "\n\n" + "\n\n".join(sections))


if __name__ == "__main__":
    run()
