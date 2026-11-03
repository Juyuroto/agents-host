import json
import os

from config import DATA_DIR

DIR = os.path.join(DATA_DIR, "historique")


def path(day: str) -> str:
    return os.path.join(DIR, f"{day}.json")


def previous(day: str) -> dict | None:
    try:
        files = sorted(f for f in os.listdir(DIR) if f.endswith(".json") and f < f"{day}.json")
    except FileNotFoundError:
        return None
    if not files:
        return None
    with open(os.path.join(DIR, files[-1]), encoding="utf-8") as f:
        return json.load(f)


def save(day: str, snapshot: dict) -> None:
    os.makedirs(DIR, exist_ok=True)
    with open(path(day), "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False)


def diff(prev: dict, cur: dict) -> list[str]:
    lines = []
    commits = len(set(cur["commits"]) - set(prev["commits"]))
    if commits:
        lines.append(f"{commits} nouveau(x) commit(s)")
    for n in sorted(set(cur["issues"]) - set(prev["issues"])):
        lines.append(f"Nouvelle issue #{n}")
    for n in sorted(set(cur["prs"]) - set(prev["prs"])):
        lines.append(f"PR ouverte #{n}")
    for n in sorted(set(prev["prs"]) - set(cur["prs"])):
        lines.append(f"PR fermée #{n}")
    if cur["ci"] != prev["ci"]:
        lines.append(f"CI : {prev['ci']} -> {cur['ci']}")
    return lines
