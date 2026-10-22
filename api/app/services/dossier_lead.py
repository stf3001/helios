"""Le dossier transmis avec une mise en relation (série 4, lot 2) — fonctions pures.

Un INSTANTANÉ de ce que le foyer a coché, figé et daté au moment du consentement. Rien d'autre :
chaque rubrique est une liste blanche de champs. Jamais le PDL, jamais un numéro de série, jamais
une note libre du carnet ni le nom d'un intervenant — aucun de ces champs n'est lu ici.

Minimum toujours transmis : code postal, type de logement, métier, message du foyer. Au choix :
le résumé de la fiche, un projet du carnet, le dernier pré-audit ou la dernière étude, des documents.
Le partenaire n'appelle que dans les créneaux donnés (démarchage interdit : art. L. 223-1 du code
de la consommation, loi 2020-901).
"""
from datetime import date, datetime

JOURS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi")
PLAGES = ("matin", "midi", "apres_midi", "soir")

# Le résumé de la fiche : ce qu'il faut pour préparer un premier appel. L'horizon et le budget y
# sont parce que le score les lit — partagés seulement si le foyer coche le résumé.
CHAMPS_FICHE = ("surface_habitable", "annee_construction", "chauffage_principal", "chauffage_principal_annee",
                "isolation_combles", "isolation_murs", "isolation_plancher", "menuiseries", "horizon",
                "budget_envisage", "completeness_score")
CHAMPS_PROJET = ("titre", "etape", "budget_bas_eur", "budget_haut_eur", "budget_source", "budget_statut",
                 "budget_date", "economie_annuelle_eur", "economie_source", "economie_statut", "economie_date")


class DossierInvalide(ValueError):
    """Un choix du foyer est incohérent : le message dit lequel."""


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def _jour(d) -> str | None:
    if d is None:
        return None
    if isinstance(d, str):
        return d[:10]
    return (d.date() if isinstance(d, datetime) else d).isoformat()


def valider_creneaux(creneaux: list[dict]) -> list[dict]:
    """Au moins un créneau ; chacun un jour et une plage connus ; sans doublon, dans l'ordre de la semaine."""
    vus = set()
    for c in creneaux or []:
        jour, plage = _champ(c, "jour"), _champ(c, "plage")
        if jour not in JOURS or plage not in PLAGES:
            raise DossierInvalide(f"Créneau inconnu : {jour} {plage}")
        vus.add((jour, plage))
    if not vus:
        raise DossierInvalide("Indiquez au moins un créneau où vous pouvez être appelé.")
    return [{"jour": j, "plage": p} for j, p in sorted(vus, key=lambda x: (JOURS.index(x[0]), PLAGES.index(x[1])))]


def resume_etude(etude: dict | None) -> dict | None:
    """Le pré-audit ou l'étude, recopié tel quel et daté : ce qui aide un professionnel, sans plus."""
    if etude is None:
        return None
    if etude["type"] == "audit":
        actions = [{"label": p.get("label"), "cout_eur": p.get("cout_eur"),
                    "economie_annuelle_eur": p.get("economie_annuelle_eur"), "horizon": p.get("horizon")}
                   for p in (etude["contenu"].get("priorites") or []) if isinstance(p, dict) and p.get("label")]
        return {"type": "audit", "date": _jour(etude["date"]), "actions": actions}
    ind = etude["contenu"].get("indicateurs") or {}
    inv = etude["contenu"].get("investissement") or {}
    return {"type": "simulateur", "date": _jour(etude["date"]), "puissance_kwc": ind.get("puissance_kwc"),
            "investissement_eur": inv.get("total_eur"), "economie_1re_annee_eur": ind.get("economie_1re_annee_eur"),
            "temps_retour_ans": ind.get("temps_retour_ans")}


def construire_dossier(house, metier: str, message: str | None, choix: dict, projet=None, etude: dict | None = None,
                       documents=(), aujourd_hui: date | None = None) -> dict:
    """L'instantané. `choix` : {"fiche": bool, "projet": bool, "etude": bool} ; `projet`, `etude`
    (`{"type", "date", "contenu"}`) et `documents` sont ceux que le foyer a choisis — passés
    seulement s'ils sont cochés, mais on ne se fie pas à l'appelant : une case décochée vide la rubrique."""
    dossier = {
        "constitue_le": (aujourd_hui or date.today()).isoformat(),
        "minimum": {"code_postal": _champ(house, "code_postal"), "type_logement": _champ(house, "type_logement"),
                    "metier": metier, "message": (message or "").strip() or None},
    }
    if choix.get("fiche"):
        dossier["fiche"] = {c: _champ(house, c) for c in CHAMPS_FICHE}
    if choix.get("projet") and projet is not None:
        dossier["projet"] = {c: _jour(_champ(projet, c)) if c.endswith("_date") else _champ(projet, c)
                             for c in CHAMPS_PROJET}
    if choix.get("etude") and etude is not None:
        dossier["etude"] = resume_etude(etude)
    if documents:
        dossier["documents"] = [{"id": str(_champ(d, "id")), "type": _champ(d, "type"),
                                 "filename": _champ(d, "filename")} for d in documents]
    return dossier
