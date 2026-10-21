import logging

from anthropic import APIError

from classifier import run_watch
from notifier import notify_discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agent-techwatch")


def run() -> None:
    try:
        resume = run_watch()
    except APIError:
        log.exception("Échec de la veille technique, rien d'envoyé")
        raise SystemExit(1)

    notify_discord("**Veille technique de la semaine**\n\n" + resume)


if __name__ == "__main__":
    run()
