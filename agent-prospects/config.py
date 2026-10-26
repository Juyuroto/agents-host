import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
DISCORD_PROSPECTS_WEBHOOK_URL = _require("DISCORD_PROSPECTS_WEBHOOK_URL")

DEPARTEMENTS = ["33", "87"]
SEARCH_DAYS = 7
MAX_SEARCHES = 5  # max_uses du web_search, par entreprise
MAX_COMPANIES_PER_RUN = 20  # borne le coût Anthropic
MIN_SCORE = 6

# Pré-filtre sur l'activité (minuscules, sans accents). Match en début de mot :
# "plomb" couvre "plomberie", "plombier".
ACTIVITY_KEYWORDS = [
    # commerce, restauration, hôtellerie
    "commerce", "vente", "boutique", "magasin", "boulanger", "patisser", "boucher", "epicerie",
    "restaura", "traiteur", "snack", "pizza", "cafe", "bar ", "hotel", "hebergement", "coiffure",
    "esthetique", "fleur", "librairie", "vetement", "fromag",
    # santé
    "medecin", "medical", "dentaire", "dentiste", "kinesith", "pharmacie", "veterinaire",
    "infirmi", "osteopath", "sante", "paramedical",
    # professions libérales
    "avocat", "juridique", "expert-comptable", "comptab", "architect", "consultant", "conseil",
    "agence", "formation", "communication", "marketing",
    # artisans / BTP
    "plomb", "electric", "batiment", "construction", "travaux", "chauffage", "menuiser",
    "maconnerie", "peinture", "couverture", "renovation", "installation", "climatisation",
    # services aux entreprises, immobilier, bureaux / informatique
    "services aux entreprises", "nettoyage", "secretariat", "immobili", "transaction", "syndic",
    "informatique", "logiciel", "numerique", "web", "developpement", "bureau", "design",
]
ACTIVITY_EXCLUDE = [
    "holding", "societe civile", "sci ", "gestion de patrimoine", "gestion de portefeuille",
    "participation", "acquisition", "location de tous biens", "gestion de tous biens","location meubl", "location de logement", "transport routier",
    "transport de marchandises", "industri", "fabrication", "banque", "bancaire",
    "assurance", "courtage en assurance",
]
