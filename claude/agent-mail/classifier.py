import json
import re
import logging
from anthropic import Anthropic, APIError
from config import ANTHROPIC_API_KEY

log = logging.getLogger("agent-mail")

claude = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "Tu es un agent qui analyse des mails reçus pour une entreprise de support IT (SafOps). "
    "Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, sans balises markdown, "
    "au format exact :\n"
    '{"summary": "résumé en 2-3 lignes en français", '
    '"urgency": "Faible" | "Moyenne" | "Haute", '
    '"folder": "Urgent" | "Admin" | "Clients" | "Factures" | "Fournisseurs" | "Pub"}\n'
    "Règles : si le mail nécessite une action rapide (urgency=Haute), folder=Urgent "
    "même s'il concerne un client/une facture. Sinon, classe par thème : Admin "
    "(démarches administratives, CAF/Urssaf/impôts...), Clients (demandes/échanges clients), "
    "Factures (factures reçues/émises, paiements), Fournisseurs (échanges avec fournisseurs), "
    "Pub (newsletters, publicités, offres commerciales non sollicitées)."
)

MAX_BODY_CHARS = 3000


def _extract_json(raw: str) -> str:

    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def classify_email(sender: str, subject: str, body: str) -> dict:
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
        raw = response.content[0].text
        return json.loads(_extract_json(raw))
    except (APIError, json.JSONDecodeError):
        log.exception("Erreur lors de la classification du mail")
        return {
            "summary": "Impossible de classer ce mail (erreur).",
            "urgency": "Moyenne",
            "folder": "Admin",
        }