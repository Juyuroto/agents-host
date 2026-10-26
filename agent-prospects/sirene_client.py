import logging
from datetime import date, timedelta

import requests

from config import DEPARTEMENTS, NAF_CODES, SEARCH_DAYS

log = logging.getLogger("agent-prospects")

URL = "https://recherche-entreprises.api.gouv.fr/search"
PER_PAGE = 25  # maximum accepté par l'API
# L'API n'a pas de filtre sur la date de création : on filtre côté client,
# donc on borne le nombre de pages parcourues.
MAX_PAGES = 40


def fetch_companies() -> list[dict]:
    since = (date.today() - timedelta(days=SEARCH_DAYS)).isoformat()
    params = {
        "departement": ",".join(DEPARTEMENTS),
        "activite_principale": ",".join(NAF_CODES),
        "etat_administratif": "A",
        "per_page": PER_PAGE,
    }
    companies = []
    for page in range(1, MAX_PAGES + 1):
        try:
            r = requests.get(URL, params={**params, "page": page}, timeout=15)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            log.exception("Échec de l'appel à l'API Sirene")
            return companies
        for e in data.get("results", []):
            siege = e.get("siege") or {}
            created = e.get("date_creation") or ""
            if created < since or siege.get("departement") not in DEPARTEMENTS:
                continue
            companies.append({
                "nom": e.get("nom_complet"),
                "siren": e.get("siren"),
                "naf": e.get("activite_principale"),
                "ville": siege.get("libelle_commune"),
                "code_postal": siege.get("code_postal"),
                "dirigeants": [
                    d.get("denomination") or f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()
                    for d in e.get("dirigeants") or []
                ],
                "date_creation": created,
            })
        if page >= data.get("total_pages", 0):
            break
    return companies
