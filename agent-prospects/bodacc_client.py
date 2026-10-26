import json
import logging
import re
import unicodedata
from datetime import date, timedelta

import requests

from config import ACTIVITY_EXCLUDE, ACTIVITY_KEYWORDS, DEPARTEMENTS, SEARCH_DAYS

log = logging.getLogger("agent-prospects")

URL = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records"
PAGE_SIZE = 100
MAX_PAGES = 10
FIELDS = "dateparution,numerodepartement,commercant,ville,cp,registre,listeetablissements,listepersonnes,url_complete"


def _dirigeant(raw: str | None) -> str:
    try:
        personne = json.loads(raw or "{}").get("personne") or {}
    except (ValueError, AttributeError):
        return ""
    if personne.get("typePersonne") == "pp":
        return f"{personne.get('prenom') or ''} {personne.get('nom') or ''}".strip()
    return personne.get("administration") or ""


def _activite(raw: str | None) -> str:
    try:
        etab = json.loads(raw or "{}").get("etablissement") or {}
    except (ValueError, AttributeError):
        return ""
    if isinstance(etab, list):
        etab = etab[0] if etab and isinstance(etab[0], dict) else {}
    return etab.get("activite") or ""


def _norm(s: str | None) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _pattern(words: list[str]) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(re.escape(_norm(w)) for w in words) + ")")


_KEEP, _DROP = _pattern(ACTIVITY_KEYWORDS), _pattern(ACTIVITY_EXCLUDE)


def matches_activity(activite: str | None) -> bool:
    a = _norm(activite) + " "
    return bool(a.strip()) and bool(_KEEP.search(a)) and not _DROP.search(a)


def filter_companies(companies: list[dict]) -> list[dict]:
    kept = [c for c in companies if matches_activity(c.get("activite"))]
    log.info("Pré-filtre activité : %d -> %d entreprises", len(companies), len(kept))
    return kept


def fetch_companies() -> list[dict]:
    since = (date.today() - timedelta(days=SEARCH_DAYS)).isoformat()
    depts = ",".join(f'"{d}"' for d in DEPARTEMENTS)
    params = {
        "where": f"dateparution>=date'{since}' AND familleavis=\"creation\" AND numerodepartement IN ({depts})",
        "order_by": "dateparution desc",
        "select": FIELDS,
        "limit": PAGE_SIZE,
    }
    companies, seen = [], set()
    for page in range(MAX_PAGES):
        try:
            r = requests.get(URL, params={**params, "offset": page * PAGE_SIZE}, timeout=15)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            log.exception("Échec de l'appel à l'API BODACC")
            return companies
        results = data.get("results", [])
        for e in results:
            siren = "".join((e.get("registre") or [""])[0].split())
            if not siren or siren in seen:
                continue
            seen.add(siren)
            companies.append({
                "nom": e.get("commercant"),
                "siren": siren,
                "activite": _activite(e.get("listeetablissements")),
                "ville": e.get("ville"),
                "code_postal": e.get("cp"),
                "date_parution": e.get("dateparution"),
                "dirigeant": _dirigeant(e.get("listepersonnes")),
                "lien": e.get("url_complete"),
            })
        if len(results) < PAGE_SIZE:
            break
    return companies
