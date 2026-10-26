import logging

from anthropic import APIError

from classifier import qualify
from config import MAX_COMPANIES_PER_RUN
from notifier import notify_discord
from bodacc_client import fetch_companies, filter_companies

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-prospects")


def format_prospect(p: dict) -> str:
    return (
        f"**{p['nom']}** (SIREN {p['siren']})\n"
        f"Activité : {p['activite']} · {p['ville']} ({p['code_postal']}) · Score : {p['score']}/10\n"
        f"Présence en ligne : {p['presence_en_ligne']}\n"
        f"Angle : {p['angle']}"
    )


def run() -> None:
    companies = filter_companies(fetch_companies())[:MAX_COMPANIES_PER_RUN]
    log.info("%d entreprises récentes à analyser", len(companies))
    try:
        prospects = qualify(companies)
    except APIError:
        log.exception("API Anthropic indisponible, rien d'envoyé")
        raise SystemExit(1)

    if not prospects:
        log.info("Aucun prospect qualifié")
        return
    prospects.sort(key=lambda p: p["score"], reverse=True)
    notify_discord(
        "**Prospects de la semaine**\n\n" + "\n\n".join(format_prospect(p) for p in prospects)
    )


if __name__ == "__main__":
    run()
