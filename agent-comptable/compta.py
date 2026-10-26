"""Données comptables SafOps : CSV (UTF-8 BOM, ';', virgule décimale), pièces, git local."""
import csv
import json
import re
import subprocess
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from config import COMPTA_DIR

ROOT = Path(COMPTA_DIR)
LIGNES_HEADER = ["date", "libelle", "categorie", "montant_ht", "taux_tva", "montant_tva",
                 "montant_ttc", "moyen_paiement", "statut", "piece"]
HEADERS = {
    "depenses-2026.csv": LIGNES_HEADER,
    "recettes-2026.csv": LIGNES_HEADER,
    "budgets-2026.csv": ["mois", "categorie", "budget_prevu"],
    "recurrents.csv": ["libelle", "categorie", "montant_ttc", "frequence", "jour", "actif"],
}
STATUTS = ("payé", "en attente", "annulé")
FREQUENCES = ("mensuel", "trimestriel", "annuel")
PIECE_EXT = (".pdf", ".png", ".jpg", ".jpeg")

CATEGORIES_MD = """# Catégories (figées : modification sur demande uniquement)

## Dépenses
- Matériel informatique
- Logiciels et abonnements
- Hébergement et serveurs
- Nom de domaine
- Télécom et internet
- Électricité
- Fournitures de bureau
- Petit équipement
- Déplacements
- Repas
- Frais bancaires
- Sous-traitance
- Formation
- Assurance
- Comptabilité et juridique
- Publicité et marketing

## Recettes
- Prestations de services
- Ventes de produits
- Abonnements clients
- Autres recettes
"""

README_MD = """# Suivi comptable SafOps

Suivi/analyse, pas la compta légale (Abby).

## Format
- CSV UTF-8 avec BOM, séparateur `;`, décimales à la virgule (12,50).
- Dates AAAA-MM-JJ, mois AAAA-MM, taux_tva à la virgule (20, 5,5, 0), montant_tva 0 si pas de TVA.
- statut : payé, en attente, annulé. frequence : mensuel, trimestriel, annuel. actif : oui, non. jour : 1 à 31.
- montant_ttc = montant_ht + montant_tva (à 0,01 € près).
- Catégories : voir categories.md (figées).

## Conventions
- Pièces dans `pieces/`, nommées `AAAA-MM-JJ_libelle.ext`, nom reporté dans la colonne `piece`.
- Git local : commit avant et après chaque écriture, jamais de push.
"""


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), "-c", "user.name=agent-comptable",
                           "-c", "user.email=agent-comptable@localhost", *args],
                          capture_output=True, text=True)


def commit(message: str) -> None:
    """Commit de l'état courant ; rien si aucun changement."""
    _git("add", "-A")
    if _git("diff", "--cached", "--quiet").returncode == 0:
        return
    r = _git("commit", "-m", message)
    if r.returncode != 0:
        raise RuntimeError(f"git commit a échoué : {r.stderr.strip()}")


def _write_csv(path: Path, header: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerow(header)


def init() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "pieces").mkdir(exist_ok=True)
    for name, header in HEADERS.items():
        if not (ROOT / name).exists():
            _write_csv(ROOT / name, header)
    if not (ROOT / "categories.md").exists():
        (ROOT / "categories.md").write_text(CATEGORIES_MD, encoding="utf-8")
    if not (ROOT / "README.md").exists():
        (ROOT / "README.md").write_text(README_MD, encoding="utf-8")
    # git ne suit pas un dossier vide
    if not (ROOT / "pieces" / ".gitkeep").exists():
        (ROOT / "pieces" / ".gitkeep").touch()
    if not (ROOT / ".git").exists():
        _git("init")
    commit("[ADD] Initialisation des données comptables")


def categories(kind: str) -> list[str]:
    titre = "Dépenses" if kind == "depense" else "Recettes"
    section = re.search(rf"^## {titre}\n(.*?)(?=^## |\Z)",
                        (ROOT / "categories.md").read_text(encoding="utf-8"), re.S | re.M)
    return re.findall(r"^- (.+)$", section.group(1), re.M) if section else []


def _path(nom: str) -> Path:
    if "/" in nom or "\\" in nom or nom.startswith("."):
        raise ValueError("Nom de fichier invalide")
    p = ROOT / nom
    if not p.is_file() or p.suffix not in (".csv", ".md"):
        raise ValueError(f"Fichier introuvable : {nom}")
    return p


def lire_fichier(nom: str) -> str:
    return _path(nom).read_text(encoding="utf-8-sig")


def lister_lignes(nom: str, mois: str | None = None) -> str:
    if not nom.endswith(".csv"):
        raise ValueError("Fichier CSV attendu")
    with _path(nom).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    if mois:
        rows = [r for r in rows if (r.get("date") or r.get("mois", "")).startswith(mois)]
    return json.dumps(rows, ensure_ascii=False)


def _dec(value, champ: str) -> Decimal:
    try:
        return Decimal(str(value).replace(",", ".").strip())
    except InvalidOperation:
        raise ValueError(f"{champ} invalide : {value!r}")


def _fmt(d: Decimal, places: int = 2) -> str:
    return f"{d:.{places}f}".replace(".", ",")


def _slug(libelle: str) -> str:
    s = unicodedata.normalize("NFKD", libelle).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "piece"


def ajouter_ligne(kind: str, data: dict, piece: tuple[str, bytes] | None = None,
                  creer_annee: bool = False) -> str:
    """Valide tout, puis : commit avant, écriture (pièce + ligne), commit après."""
    if kind not in ("depense", "recette"):
        raise ValueError("type doit être 'depense' ou 'recette'")
    d = date.fromisoformat(str(data.get("date", "")))
    libelle = str(data.get("libelle", "")).strip()
    if not libelle:
        raise ValueError("libelle manquant : demander à l'utilisateur")
    if data.get("categorie") not in categories(kind):
        raise ValueError(f"Catégorie hors liste : {data.get('categorie')!r}. Liste : {categories(kind)}")
    if data.get("statut") not in STATUTS:
        raise ValueError(f"statut doit être parmi {STATUTS}")
    for champ in ("montant_ht", "taux_tva", "montant_tva", "montant_ttc", "moyen_paiement"):
        if data.get(champ) in (None, ""):
            raise ValueError(f"{champ} manquant : demander à l'utilisateur, ne rien inventer")
    ht, tva, ttc = (_dec(data[c], c) for c in ("montant_ht", "montant_tva", "montant_ttc"))
    taux = _dec(data["taux_tva"], "taux_tva")
    if abs(ht + tva - ttc) > Decimal("0.01"):
        raise ValueError(f"Incohérence : HT {ht} + TVA {tva} = {ht + tva} != TTC {ttc} (écart > 0,01 €). "
                         "Rien n'a été écrit ; signaler à l'utilisateur.")
    fichier = ROOT / f"{kind}s-{d.year}.csv"
    if not fichier.exists():
        if not creer_annee:
            return (f"{fichier.name} n'existe pas. Demander confirmation à l'utilisateur "
                    "avant de créer l'année (puis rappeler avec creer_annee=true).")
    piece_nom = ""
    if piece:
        ext = Path(piece[0]).suffix.lower()
        if ext not in PIECE_EXT:
            raise ValueError(f"Extension de pièce non acceptée : {ext}")
        piece_nom = f"{d.isoformat()}_{_slug(libelle)}{ext}"
        n = 2
        while (ROOT / "pieces" / piece_nom).exists():
            piece_nom = f"{d.isoformat()}_{_slug(libelle)}-{n}{ext}"
            n += 1

    commit(f"[MODIFY] État avant ajout {kind} {d.isoformat()}")
    if not fichier.exists():
        _write_csv(fichier, LIGNES_HEADER)
    if piece:
        (ROOT / "pieces" / piece_nom).write_bytes(piece[1])
    ligne = [d.isoformat(), libelle, data["categorie"], _fmt(ht), format(taux.normalize(), "f").replace(".", ","), _fmt(tva), _fmt(ttc), str(data["moyen_paiement"]).strip(),
             data["statut"], piece_nom]
    with fichier.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerow(ligne)
    commit(f"[ADD] {kind} {d.isoformat()} {libelle[:50]}")
    return f"Ligne ajoutée dans {fichier.name}" + (f", pièce {piece_nom}" if piece_nom else "")
