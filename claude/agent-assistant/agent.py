import logging
from datetime import datetime
from anthropic import AsyncAnthropic

from config import ANTHROPIC_API_KEY, TIMEZONE
from tools import TOOLS, execute

log = logging.getLogger("agent-assistant")

claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-haiku-5-5"
MAX_TURNS = 5

SYSTEM_PROMPT = """Tu es l'assistant personnel d'Alain sur Discord. Tu l'aides à s'organiser au quotidien :
- Si on te demande de rappeler quelque chose plus tard ("rappelle-moi dans 1h de...", "demain à 14h..."), utilise le tool set_reminder
- Si on te demande d'ajouter quelque chose à son emploi du temps, utilise le tool add_agenda_item
- Si on te demande ce qui est prévu/en attente, utilise list_reminders

Réponds toujours de façon brève et directe en français, confirme simplement l'action effectuée (ex: "Noté, je te rappelle dans 1h."). Pas de blabla, pas de formules de politesse inutiles."""


async def reply(message: str) -> str:
    now = datetime.now(TIMEZONE).isoformat(timespec="minutes")
    system = SYSTEM_PROMPT + f"\n\nDate et heure actuelles : {now}"
    messages = [{"role": "user", "content": message}]
    try:
        for _ in range(MAX_TURNS):
            response = await claude.messages.create(
                model=MODEL, max_tokens=1000, system=system, tools=TOOLS, messages=messages
            )
            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if b.type == "text").strip() or "(pas de réponse)"
            messages.append({"role": "assistant", "content": response.content})
            results = [
                {"type": "tool_result", "tool_use_id": b.id, "content": execute(b.name, b.input)}
                for b in response.content
                if b.type == "tool_use"
            ]
            messages.append({"role": "user", "content": results})
        return "Je n'ai pas pu terminer, réessaie."
    except Exception:
        log.exception("Erreur lors de la réponse de l'assistant")
        return "Erreur de l'assistant, réessaie plus tard."
