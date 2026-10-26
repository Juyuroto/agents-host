import json
import os

from config import DATA_DIR

PATH = os.path.join(DATA_DIR, "suivis.json")


def load() -> list[str]:
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save(names: list[str]) -> None:
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(names), f, ensure_ascii=False)


def parse_command(text: str) -> tuple[str, str] | None:
    words = text.strip().split()
    low = [w.lower() for w in words]
    if low == ["suivis"]:
        return "suivis", ""
    if low[:3] == ["ne", "plus", "suivre"] and len(words) == 4:
        return "retirer", words[3]
    if low[:1] == ["suivre"] and len(words) == 2:
        return "ajouter", words[1]
    return None


def _match(name: str, candidates: list[str]) -> str | None:
    n = name.lower()
    return next((c for c in candidates if n in (c.lower(), c.lower().split("/")[-1])), None)


def execute(action: str, name: str, list_repos) -> str:
    names = load()
    if action == "suivis":
        return "Dépôts suivis :\n" + "\n".join(f"- {n}" for n in names) if names else "Aucun dépôt suivi."
    if action == "retirer":
        found = _match(name, names)
        if not found:
            return f"Dépôt non suivi : {name}"
        save([n for n in names if n != found])
        return f"Dépôt retiré : {found}"
    found = _match(name, [r["full_name"] for r in list_repos()])
    if not found:
        return f"Dépôt inconnu : {name}"
    if found not in names:
        save(names + [found])
    return f"Dépôt suivi : {found}"
