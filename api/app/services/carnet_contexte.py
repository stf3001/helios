"""Le carnet de maison résumé pour le chat — fonctions pures (carnet, lot 5).

COURT ET ANONYME, pour deux raisons qui tiennent ensemble : le modèle local (llama3.2:3b) a
une fenêtre courte, et le même résumé partira un jour vers une API externe. On n'envoie donc
que des CODES (catégorie, type, statut, nature) et des DATES — jamais un texte saisi par le
foyer : ni numéro de série, ni note, ni installateur, ni intervenant, ni entreprise, ni titre
de journal, ni nom de fichier, ni montant. La nature d'un chantier, texte libre, est réduite
à une catégorie par mots-clés.

Chaque élément porte son statut : `declare` (saisi par le foyer), `calcule` (déduit d'une
date exacte), `suppose` (déduit d'une année seule).
"""
import json
import re
from datetime import date

# 2 000 caractères (décision du 21/10/2026, lot 5) : à 1 500, les cinq échéances seules en
# prenaient 940 et le journal ne tenait sur aucune maison réelle.
PLAFOND_CARACTERES = 2000
MAX_EQUIPEMENTS = 12
MAX_ECHEANCES = 5
MAX_GARANTIES = 5
MAX_JOURNAL = 5
MOIS_JOURNAL = 24

# Ordre d'importance : ce qui chauffe d'abord, c'est là que sont les questions et les obligations.
_ORDRE_CATEGORIES = ("chauffage", "ecs", "clim", "production_electricite", "stockage")

# Nature d'un chantier → catégorie. Le texte saisi ne part jamais : seul le code sort.
_CATEGORIES_TRAVAUX = tuple((code, re.compile(motif)) for code, motif in (
    ("isolation", r"isol|comble|laine|ouate|\bit[ei]\b"),
    ("menuiseries", r"fen[eê]tre|menuiser|vitrage|\bportes?\b|volet"),
    ("toiture", r"toit|couverture|charpente|tuile"),
    ("chauffage", r"chauff(?!e[- ]eau)|\bpac\b|pompe [àa] chaleur|chaudi[eè]re|po[eê]le"),
    ("eau_chaude", r"ballon|chauffe[- ]eau|eau chaude"),
    ("ventilation", r"\bvmc\b|ventil"),
    ("solaire", r"solaire|photovolt|panneau"),
    ("electricite", r"[ée]lectri|tableau"),
    ("plomberie", r"plomb|canalisation|sanitaire"),
))


# Une question « sur le carnet » parle de CE foyer (« ma PAC », « mes travaux », « j'ai fait »)
# ET d'un sujet que le carnet connaît. Ces questions vont à la route API (décision de
# Stéphane, 21/10/2026) : le modèle local s'y trompait (lot 5, réponses archivées).
_POSSESSIF = re.compile(r"\b(mon|ma|mes|notre|nos)\b|\bj'ai\b|\bchez moi\b", re.IGNORECASE)
_SUJET_CARNET = re.compile(
    r"entretien|entretenir|garantie|\bâge\b|\bage\b|journal|travaux|chantier|remplace|r[ée]vision|ramonage"
    r"|[ée]ch[ée]ance|\bpac\b|pompe [àa] chaleur|chaudi[eè]re|ballon|chauffe[- ]eau|panneaux?|onduleur"
    r"|\bvmc\b|clim|po[eê]le|insert|fosse|micro[- ]station|batterie|borne|[ée]quipement|appareil",
    re.IGNORECASE,
)


def parle_du_carnet(question: str) -> bool:
    return bool(_POSSESSIF.search(question) and _SUJET_CARNET.search(question))


def _champ(obj, nom):
    return obj.get(nom) if isinstance(obj, dict) else getattr(obj, nom, None)


def categorie_travaux(nature: str | None) -> str:
    texte = (nature or "").lower()
    for code, motif in _CATEGORIES_TRAVAUX:
        if motif.search(texte):
            return code
    return "autres_travaux"


def _iso(d) -> str | None:
    return d.isoformat() if hasattr(d, "isoformat") else d


def choisir_echeances(echeances: list[dict]) -> list[dict]:
    """Au plus une échéance par équipement (et une pour la maison), les OBLIGATIONS d'abord.

    Décision du 21/10/2026 (lot 5) : en prenant simplement les 5 plus urgentes, les tâches
    mensuelles « en retard » faute de journal occupaient toutes les places, et l'entretien
    légal d'une PAC fait en mars (prochaine échéance dans deux ans) n'y entrait jamais. Le
    résultat garde l'ordre d'urgence du moteur.
    """
    choisies, vus = [], set()
    for nature in ("obligation", "recommande"):
        for i, e in enumerate(echeances):
            cle = e["equipement_id"] or "maison"
            if e["nature"] != nature or cle in vus or len(choisies) == MAX_ECHEANCES:
                continue
            vus.add(cle)
            choisies.append((i, e))
    return [e for _, e in sorted(choisies, key=lambda c: c[0])]


def taille(carnet: dict) -> int:
    """La longueur telle que le prompt la sérialise (`rag.build_user_content`)."""
    return len(json.dumps(carnet, ensure_ascii=False, default=str))


def carnet_contexte(equipements, echeances, garanties, journal, resume_pieces=None,
                    aujourd_hui: date | None = None, travaux=(), risques: dict | None = None,
                    vigilance: list | None = None) -> dict:
    """Le résumé du carnet ; `{}` si le foyer n'a rien saisi.

    `equipements` : modèles ou dicts portant aussi `age_ans` / `age_statut` (calculés par
    `garanties.age_ans`) ; `echeances` : sortie triée du moteur d'entretien ; `garanties` :
    sortie de `garanties_maison` ; `journal` : sortie de `journal_fusionne` (plus récent
    d'abord) ; `travaux` : pour réduire la nature d'un chantier à sa catégorie ; `risques` :
    `risques_affichage.pour_le_chat` (codes des risques de la COMMUNE, statut `observe`, < 200 car.) ;
    `vigilance` : `vigilance.pour_le_chat` (orange ou rouge en cours : phénomène, couleur, fin).
    """
    aujourd_hui = aujourd_hui or date.today()
    type_par_id = {_champ(e, "id"): _champ(e, "type") for e in equipements}
    nature_par_travaux = {_champ(t, "id"): _champ(t, "nature") for t in travaux}

    en_service = [e for e in equipements if _champ(e, "en_service") is not False]
    rang = {c: i for i, c in enumerate(_ORDRE_CATEGORIES)}
    en_service.sort(key=lambda e: rang.get(_champ(e, "categorie"), len(rang)))
    eqs = []
    for e in en_service[:MAX_EQUIPEMENTS]:
        ligne = {"categorie": _champ(e, "categorie"), "type": _champ(e, "type")}
        if _champ(e, "marque"):
            ligne["marque"] = _champ(e, "marque")
        if _champ(e, "age_ans") is not None:
            ligne["age_ans"] = _champ(e, "age_ans")
            ligne["statut"] = _champ(e, "age_statut") or "calcule"
        else:
            ligne["statut"] = "declare"
        if _champ(e, "contrat_entretien") is not None:
            ligne["contrat_entretien"] = _champ(e, "contrat_entretien")
        eqs.append(ligne)

    echs = []
    for e in choisir_echeances(echeances):
        ligne = {
            "tache": e["libelle"],  # texte de la table d'entretien, relu — pas une saisie du foyer
            "pour": type_par_id.get(e["equipement_id"], "maison") if e["equipement_id"] else "maison",
        }
        if e["echeance"]:  # une tâche « à planifier » n'a pas de date : la clé est omise
            ligne["date"] = _iso(e["echeance"])
        ligne.update({
            "statut": e["statut"], "nature": e["nature"], "qui": e["qui"],
            "donnees": "suppose" if e.get("reference_supposee") else ("calcule" if e["echeance"] else "declare"),
        })
        echs.append(ligne)

    # Garanties regroupées par objet : un chantier donne UNE ligne et ses trois fins, pas trois
    # lignes répétant l'objet et le statut. Le plafond de 1 500 caractères l'impose.
    gars, par_objet = [], {}
    for g in garanties:
        if g["statut"] == "expiree":
            continue
        objet = (type_par_id.get(g["source_id"]) if g["provenance"] == "equipement"
                 else categorie_travaux(nature_par_travaux.get(g["source_id"])))
        cle = (g["provenance"], g["source_id"])
        if cle not in par_objet:
            if len(gars) == MAX_GARANTIES:
                continue
            par_objet[cle] = {"objet": objet, "statut": g["donnees"], "fin": {}}
            gars.append(par_objet[cle])
        par_objet[cle]["fin"][g["code"]] = _iso(g["fin"])

    limite = date(aujourd_hui.year - MOIS_JOURNAL // 12, aujourd_hui.month, min(aujourd_hui.day, 28))
    jrn = []
    for l in journal:
        d = l["date"]
        if d is None or d < limite:
            continue
        ligne = {"date": _iso(d), "type": l["type"], "justifie": bool(l["justifie"])}
        if l.get("equipement_id"):
            ligne["pour"] = type_par_id.get(l["equipement_id"])
        jrn.append(ligne)
        if len(jrn) == MAX_JOURNAL:
            break

    pieces = None
    if resume_pieces and resume_pieces["nb_pieces"]["valeur"]:
        pieces = {"nombre": resume_pieces["nb_pieces"]["valeur"], "statut": "declare"}
        if resume_pieces["surface_pieces_m2"]["valeur"]:
            pieces["surface_m2"] = resume_pieces["surface_pieces_m2"]["valeur"]
        if resume_pieces["emetteurs_par_type"]:
            pieces["emetteurs"] = {e["type"]: e["nombre"] for e in resume_pieces["emetteurs_par_type"]}
        if resume_pieces["chauffees_sans_emetteur"]["valeur"]:
            pieces["chauffees_sans_emetteur"] = len(resume_pieces["chauffees_sans_emetteur"]["valeur"])

    # Un foyer qui n'a rien saisi n'a pas de carnet, même si la table connaît des tâches de
    # maison (détecteur de fumée) : on ne lui résumerait que des « à planifier ».
    if not (equipements or travaux or journal or pieces or risques or vigilance):
        return {}
    carnet = {"equipements": eqs, "echeances": echs, "garanties": gars, "journal": jrn, "pieces": pieces,
              "risques": risques, "vigilance": vigilance}
    carnet = {k: v for k, v in carnet.items() if v}  # aucun bloc vide
    return _plafonner(carnet)


def _plafonner(carnet: dict) -> dict:
    """Sous le plafond, en coupant dans l'ordre décidé : le journal (du plus ancien au plus
    récent), les pièces, puis les équipements de FAIBLE priorité — ceux qui suivent les trois
    premiers (chauffage, eau chaude, clim passent en tête). Si cela ne suffit pas, on réduit
    garanties et échéances sans les vider, et ce n'est qu'en dernier recours que les
    équipements prioritaires partent : un carnet sans un seul appareil ne répondrait plus à
    « quel âge a mon chauffe-eau ? ».
    """
    etapes = (("journal", 0), ("pieces", 0), ("equipements", 3), ("garanties", 2), ("echeances", 3),
              ("garanties", 0), ("equipements", 1), ("echeances", 1), ("equipements", 0), ("echeances", 0))
    for bloc, garder in etapes:
        while taille(carnet) > PLAFOND_CARACTERES and bloc in carnet:
            valeur = carnet[bloc]
            if isinstance(valeur, list) and len(valeur) > max(garder, 1):
                valeur.pop()
            elif garder == 0:
                del carnet[bloc]
            else:
                break
    return carnet
