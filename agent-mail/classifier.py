import logging
from anthropic import Anthropic, APIError
from config import ANTHROPIC_API_KEY

log = logging.getLogger("agent-mail")

claude = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "Tu es un agent qui résume des mails reçus pour une notification Discord. "
    "Réponds en français, en 2-3 lignes max : résumé du contenu + niveau d'urgence "
    "(Faible / Moyenne / Haute). Sois concis, pas de blabla."
)

MAX_BODY_CHARS = 3000


def classify_email(sender: str, subject: str, body: str) -> str:
    snippet = body[:MAX_BODY_CHARS]

    try:
        response = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"De : {sender}\nSujet : {subject}\n\n{snippet}",
                }
            ],
        )
        return response.content[0].text
    except APIError:
        log.exception("Erreur API Claude lors de la classification du mail")
        return "Impossible de résumer ce mail (erreur API)."