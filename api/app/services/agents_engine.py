"""Agents automatisés — doc 10 J10 : crawler d'ingestion + veille, alimentant le RAG.

Unifie l'ingestion : au lieu du script manuel, des *sources* déclarées sont parcourues,
parsées, embarquées (embeddings) et upsertées dans kb_documents/kb_chunks. Chaque exécution
est journalisée dans agents_log. La veille repère les contenus périmés (aides/prix) à rafraîchir.
"""
import calendar
import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog
from app.models.kb import KbChunk, KbDocument
from app.services.ollama_client import embed

_REPO_ROOT = Path(__file__).resolve().parents[3].parent  # dossier HELIOS (parent de helios/)


@dataclass
class SourceSpec:
    name: str          # identifiant stocké dans kb_documents.source
    kind: str          # "faq_markdown" | "web"
    location: str      # chemin de fichier (relatif à HELIOS/) ou URL
    cat: str | None = None
    verif: str | None = None
    #: Nature de la source (migration 0022) — écrite dans `kb_documents.fiabilite`.
    #: C'était déduit du TYPE de fichier : « officiel » pour tout markdown, « veille » pour
    #: tout le web. C'était faux, et de façon gênante — les cas pratiques sont des profils
    #: FICTIFS et la fiche VOSS une hypothèse de lancement, les deux étaient annoncées
    #: « officiel ». Déclaré ici, donc relisible d'un coup d'œil.
    #: officiel (texte de loi, barème publié) | maison (rédigé par HELIOS depuis ses
    #: sources) | constructeur | hypothese | pedagogique (fictif) | veille (web non relu).
    fiabilite: str = "maison"
    #: Cadence de RE-VÉRIFICATION, en mois, pour une source dont le contenu se périme
    #: (barèmes, échéances, grilles tarifaires). À défaut d'une fin de validité écrite dans
    #: la fiche, la veille signalera le document ce nombre de mois après son dernier
    #: changement de contenu. C'est un rythme de surveillance, pas une affirmation sur la
    #: durée de vie d'une aide : rien n'est retiré de la base, une ligne est journalisée.
    validite_mois: int | None = None


# Registre des sources. La FAQ locale est la source canonique (fiable, hors réseau).
# Les sources "web" (aides/prix) sont optionnelles : un échec réseau est journalisé, non bloquant.
SOURCES: list[SourceSpec] = [
    # Source historique (109 fiches d'origine). Déplacée depuis HELIOS/05-FAQ-V1.md vers le
    # dépôt le 27/07/2026 : elle vit désormais avec les autres fiches, donc versionnée en git.
    SourceSpec(name="faq_maison", kind="faq_markdown", location="helios/kb/faq_maison.md"),
    SourceSpec(name="solutions", kind="faq_markdown", location="helios/kb/solutions.md"),
    SourceSpec(name="pilotage", kind="faq_markdown", location="helios/kb/pilotage.md"),
    SourceSpec(name="eau", kind="faq_markdown", location="helios/kb/eau.md"),
    SourceSpec(name="autoconso", kind="faq_markdown", location="helios/kb/autoconso.md"),
    SourceSpec(name="complements", kind="faq_markdown", location="helios/kb/complements.md"),
    # Profils-types FICTIFS, à but pédagogique : jamais le foyer qui lit. Le prompt le dit
    # déjà au modèle (rag.build_user_content) ; la base le dit maintenant aussi.
    SourceSpec(name="cas_pratiques", kind="faq_markdown", location="helios/kb/cas_pratiques.md",
               fiabilite="pedagogique"),
    # Barèmes publiés, et ce qui se périme le plus vite de toute la base : plafonds de
    # revenus, montants par geste, CEE, taux de TVA. Déjà tagués `verif:date_sensible_*`
    # dans le markdown, mais rien ne savait lire ce tag.
    SourceSpec(name="baremes_aides", kind="faq_markdown", location="helios/kb/baremes_aides.md",
               fiabilite="officiel", validite_mois=12),
    SourceSpec(name="confort_ete", kind="faq_markdown", location="helios/kb/confort_ete.md"),
    # Échéances de la loi Climat, obligations d'audit et d'entretien : du texte de loi, avec
    # des dates qui tombent.
    SourceSpec(name="reglementation", kind="faq_markdown", location="helios/kb/reglementation.md",
               fiabilite="officiel", validite_mois=12),
    # Specs commerciales de lancement fournies par le fabricant — explicitement une
    # hypothèse (`verif:hypothese_lancement`), pas un relevé.
    SourceSpec(name="voss", kind="faq_markdown", location="helios/kb/voss.md",
               fiabilite="hypothese"),
    # Faits juridiques vérifiés (loi n° 2025-594, délais de rétractation, amendes).
    SourceSpec(name="vigilance", kind="faq_markdown", location="helios/kb/vigilance.md",
               fiabilite="officiel"),
    # Sources de terrain (109 fiches, ajoutees le 28/09/2026). Tirees de syntheses clients
    # anonymisees : elles apportent ce que la FAQ d'origine ignorait, notamment les contrats
    # d'obligation d'achat (resiliation, indemnite) et le raisonnement sur l'existant.
    SourceSpec(name="terrain", kind="faq_markdown", location="helios/kb/terrain.md"),
    SourceSpec(name="pac_air_eau", kind="faq_markdown", location="helios/kb/pac_air_eau.md"),
    SourceSpec(name="pac_air_air", kind="faq_markdown", location="helios/kb/pac_air_air.md"),
    SourceSpec(name="ecs_solaire", kind="faq_markdown", location="helios/kb/ecs_solaire.md"),
    SourceSpec(name="stockage_contrats", kind="faq_markdown", location="helios/kb/stockage_contrats.md"),
    SourceSpec(name="autonomie_hors_reseau", kind="faq_markdown", location="helios/kb/autonomie_hors_reseau.md"),
    SourceSpec(name="dimensionnement_pv", kind="faq_markdown", location="helios/kb/dimensionnement_pv.md"),
    SourceSpec(name="supports_securite", kind="faq_markdown", location="helios/kb/supports_securite.md"),
    SourceSpec(name="urbanisme_assurance", kind="faq_markdown", location="helios/kb/urbanisme_assurance.md"),
    SourceSpec(name="financement_projet", kind="faq_markdown", location="helios/kb/financement_projet.md"),
    SourceSpec(name="cas_terrain", kind="faq_markdown", location="helios/kb/cas_terrain.md"),
    # Fin de contrat de rachat et ajout de puissance (28/09/2026) : deux situations que la
    # base ignorait, alors qu'elles representent une bonne part des appels recus.
    SourceSpec(name="fin_contrat_rachat", kind="faq_markdown", location="helios/kb/fin_contrat_rachat.md"),
    # Parcours (28/09/2026) : l'ordre des decisions, verse en fiches quand la section Guides
    # a ete supprimee. Chez Helios on interroge le robot, on ne parcourt pas des pages.
    SourceSpec(name="parcours", kind="faq_markdown", location="helios/kb/parcours.md"),
    # Eolien domestique (29/09/2026), en meme temps que la page « Le vent » et que
    # l'eolienne du simulateur. Chiffres techniques du constructeur, regles d'urbanisme
    # marquees comme telles.
    SourceSpec(name="eolien", kind="faq_markdown", location="helios/kb/eolien.md"),
    # Le jardin nourricier (29/09/2026), en meme temps que la page « La terre » et que le
    # potager du simulateur. Les ordres de grandeur (kg par personne, kg/m2, heures
    # d'entretien) sont ceux de services/jardin.py : les deux doivent rester d'accord,
    # sinon le chat contredira le calculateur sur la meme page.
    SourceSpec(name="potager", kind="faq_markdown", location="helios/kb/potager.md"),
    # L'achat d'energie (30/09/2026), en meme temps que la page du meme nom. Les options
    # du tarif reglemente, la reforme des heures creuses, le courtage et sa commission.
    # Les prix y sont DATES (grille du 01/08/2026) : une grille change, une explication
    # non — c'est pour cela que les fiches expliquent d'abord et chiffrent ensuite.
    SourceSpec(name="achat_energie", kind="faq_markdown", location="helios/kb/achat_energie.md",
               validite_mois=12),
    # Le puits canadien (01/10/2026), en meme temps que la partie du meme nom sur la page
    # « La terre ». AUCUNE FICHE NE CHIFFRE UNE ECONOMIE DE FACTURE, et c'est delibere :
    # le gain depend du climat, du sol, de la ventilation et de ce qu'on chauffe. Les fiches
    # donnent des TEMPERATURES, qui se mesurent. Point 19 de TODO.md pour le calculateur.
    SourceSpec(name="puits_canadien", kind="faq_markdown", location="helios/kb/puits_canadien.md"),
    # Fin de vie et carbone du solaire (05/10/2026), en meme temps que la page « Le soleil ».
    # La base n'en disait rien alors que la page les traite : le chat ne pouvait pas suivre.
    # La fiche sur le gain climatique reel en France est volontairement decevante — c'est la
    # verite mesuree (reseau francais a 19,6 g CO2/kWh), et personne d'autre ne l'ecrira.
    SourceSpec(name="recyclage_carbone", kind="faq_markdown", location="helios/kb/recyclage_carbone.md"),
    # Verifier l'entreprise qui pose (05/10/2026), meme lot. Complete sans les redire la fiche
    # « Quelles questions poser a un installateur » (terrain) et la verification RGE (vigilance).
    SourceSpec(name="choisir_installateur", kind="faq_markdown", location="helios/kb/choisir_installateur.md"),
    # Fiches « action » du pré-audit (20/10/2026, lot A) : une source par action ou conseil
    # du moteur, rédigées par Stéphane. Structure fixe — rentable dans quel cas, diagnostic,
    # bénéfices hors euros, vigilance, devis, aides — et AUCUN chiffre universel de
    # rentabilité : les conditions sont ici, le chiffre est dans le pré-audit. La section
    # « Pour le pré-audit », après le dernier `---`, n'est pas ingérée (textes du lot 4).
    SourceSpec(name="action_combles", kind="faq_markdown", location="helios/kb/action_combles.md"),
    SourceSpec(name="action_murs", kind="faq_markdown", location="helios/kb/action_murs.md"),
    SourceSpec(name="action_plancher", kind="faq_markdown", location="helios/kb/action_plancher.md"),
    SourceSpec(name="action_menuiseries", kind="faq_markdown", location="helios/kb/action_menuiseries.md"),
    SourceSpec(name="action_ventilation", kind="faq_markdown", location="helios/kb/action_ventilation.md"),
    SourceSpec(name="action_regulation", kind="faq_markdown", location="helios/kb/action_regulation.md"),
    SourceSpec(name="action_pac_remplacement", kind="faq_markdown",
               location="helios/kb/action_pac_remplacement.md"),
    SourceSpec(name="action_pac_air_air_renouvellement", kind="faq_markdown",
               location="helios/kb/action_pac_air_air_renouvellement.md"),
    SourceSpec(name="action_ballon_thermodynamique", kind="faq_markdown",
               location="helios/kb/action_ballon_thermodynamique.md"),
    SourceSpec(name="action_contrat", kind="faq_markdown", location="helios/kb/action_contrat.md"),
    SourceSpec(name="gestes_equipements", kind="faq_markdown", location="helios/kb/gestes_equipements.md"),
    # Taux et plafonds de la rénovation d'ampleur relevés le 20/10/2026 : barèmes datés,
    # re-vérifiés plus souvent que les autres.
    SourceSpec(name="renovation_ampleur", kind="faq_markdown", location="helios/kb/renovation_ampleur.md",
               validite_mois=6),
    SourceSpec(name="lire_son_dpe", kind="faq_markdown", location="helios/kb/lire_son_dpe.md"),
    # Garanties après travaux (21/10/2026, carnet de maison lot 1) : l'écran « Travaux et
    # garanties » y renvoie au lieu d'écrire du juridique dans le code. À relire.
    SourceSpec(name="garanties_travaux", kind="faq_markdown", location="helios/kb/garanties_travaux.md"),
]

# Sources dont les fiches sont des Q/R servables telles quelles : page FAQ publique
# (routers/faq.py) et reponse instantanee sans LLM (services/rag.py). Les deux tenaient
# chacune sa propre copie de la liste, avec un commentaire demandant de les garder
# identiques — une source ajoutee etait donc oubliee d'un cote ou de l'autre. Elle se
# deduit maintenant de SOURCES : les sources "web" en sont exclues (texte decoupe a
# l'aveugle, pas des Q/R), ainsi que les sources listees ci-dessous.
# `cas_terrain` : ses intitules sont des situations (« Cas de terrain : ... »), pas des
# questions. Precieux pour le raisonnement du chat, hors sujet dans une liste de questions.
_HORS_FAQ_PUBLIQUE = ("cas_terrain",)

SOURCES_QR: tuple[str, ...] = tuple(
    s.name for s in SOURCES if s.kind == "faq_markdown" and s.name not in _HORS_FAQ_PUBLIQUE
)

_FAQ_RE = re.compile(
    r"^### Q:\s*(?P<question>.+?)\s*\n`(?P<meta>[^`]+)`\s*\n"
    r"R:\s*(?P<answer>.+?)(?=\n### Q:|\n## |\n---|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _parse_meta(meta: str) -> dict:
    out: dict = {}
    for part in meta.split("|"):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        key, value = key.strip(), value.strip()
        out[key] = [t.strip() for t in value.split(",") if t.strip()] if key == "tags" else value
    return out


def parse_faq_markdown(text: str) -> list[dict]:
    """Parse un fichier FAQ (### Q: / `meta` / R:) en entrées {titre, content, metadata}.

    Deux clés de métadonnées sont reconnues en plus depuis la migration 0022, toutes deux
    facultatives : `valide:<AAAA-MM-JJ>` (fin de validité de CETTE fiche, qui l'emporte sur
    la cadence de la source) et `zone:<département ou région>` pour une aide locale. La
    conversion de la date est faite par `crawl_source`, qui peut journaliser une faute de
    frappe — ici on reste un parseur pur, sans base de données.

    Les clés inconnues restent ignorées, `seo_titre`/`seo_desc` comprises : elles n'ont rien
    à faire dans la base vectorielle, et le script de pré-rendu les lit de son côté.
    """
    entries = []
    for m in _FAQ_RE.finditer(text):
        question = m.group("question").strip()
        answer = m.group("answer").strip()
        meta = _parse_meta(m.group("meta"))
        entries.append({
            "titre": question,
            "content": f"Q: {question}\nR: {answer}",
            # `niveau_confiance` n'est plus écrit en dur ici : il vient de la source
            # (`SourceSpec.fiabilite`) et est posé par `_fetch_source_entries`.
            "metadata": {"cat": meta.get("cat"), "tags": meta.get("tags", []),
                         "verif": meta.get("verif")},
            "valide_brut": meta.get("valide"),
            "zone": meta.get("zone"),
        })
    return entries


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, size: int = 800) -> list[str]:
    words, chunks, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > size:
            chunks.append(cur.strip())
            cur = ""
        cur += " " + w
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


async def _fetch_source_entries(source: SourceSpec) -> list[dict]:
    """Les entrées brutes d'une source, avec la fiabilité DE LA SOURCE posée sur chacune.

    Une source « web » reste en `veille` quoi qu'elle déclare : son texte est découpé à
    l'aveugle et personne ne l'a relu. Un contenu ramené du réseau ne peut pas s'auto-
    déclarer officiel — ce serait le plus court chemin pour qu'une page quelconque prenne
    le pas sur un barème publié.
    """
    if source.kind == "faq_markdown":
        text = (_REPO_ROOT / source.location).read_text(encoding="utf-8")
        entries = parse_faq_markdown(text)
        for entry in entries:
            entry["metadata"]["niveau_confiance"] = source.fiabilite
            entry["fiabilite"] = source.fiabilite
        return entries
    if source.kind == "web":
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            res = await client.get(source.location)
            res.raise_for_status()
        text = _html_to_text(res.text)
        return [
            {"titre": f"{source.name} #{i + 1}", "content": chunk,
             "metadata": {"cat": source.cat, "tags": [], "verif": source.verif, "niveau_confiance": "veille"},
             "fiabilite": "veille", "url": source.location}
            for i, chunk in enumerate(_chunk_text(text))
        ]
    raise ValueError(f"Type de source inconnu : {source.kind}")


async def _log(db: AsyncSession, agent: str, action: str, detail: str) -> None:
    db.add(AgentLog(agent=agent, action=action, detail=detail))


async def _elaguer(db: AsyncSession, source: SourceSpec, titres_du_fichier: set[str]) -> int:
    """Retire de la base les fiches de cette source qui ne sont plus dans son fichier.

    Sans ça le crawler ne sait qu'ajouter : une fiche supprimée du markdown restait en base
    pour toujours. Elle continuait d'être listée sur /faq alors que le pré-rendu, qui lit le
    markdown, ne lui générait plus de page — le lien « ouvrir cette fiche » tombait en 404 —
    et le chat pouvait encore la servir. Constaté le 29/09/2026 sur une fiche d'éolien.

    GARDE-FOU : on n'élague jamais à partir d'un fichier qui n'a produit aucune fiche. Une
    erreur de lecture ou une expression de parsing cassée effacerait sinon la source entière,
    silencieusement. Mieux vaut une fiche périmée de trop qu'une source disparue.

    Les chunks partent avant le document : la clé étrangère n'a pas de suppression en cascade.
    """
    if not titres_du_fichier:
        return 0

    perimes = list(await db.scalars(
        select(KbDocument).where(
            KbDocument.source == source.name,
            KbDocument.titre.notin_(titres_du_fichier),
        )
    ))
    for doc in perimes:
        for chunk in await db.scalars(select(KbChunk).where(KbChunk.document_id == doc.id)):
            await db.delete(chunk)
        await db.delete(doc)
        await _log(db, "crawler", "retrait", f"{source.name}: « {doc.titre} » n'est plus dans le fichier")
    return len(perimes)


def _empreinte(content: str) -> str:
    """SHA-256 du contenu — la clé qui dit si une fiche a VRAIMENT changé (migration 0022)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _ajoute_mois(depart: date, mois: int) -> date:
    """`depart` décalé de N mois. Écrit à la main : le projet n'a pas `dateutil`.

    Le jour est ramené au dernier jour du mois d'arrivée quand il n'y existe pas
    (31 janvier + 1 mois = 28 ou 29 février).
    """
    total = depart.month - 1 + mois
    annee, mois_cible = depart.year + total // 12, total % 12 + 1
    return date(annee, mois_cible, min(depart.day, calendar.monthrange(annee, mois_cible)[1]))


def _valide_jusqu_au(source: SourceSpec, entry: dict, date_contenu: date) -> tuple[date | None, str | None]:
    """Fin de validité de ce document, et le message d'anomalie à journaliser le cas échéant.

    LA FICHE L'EMPORTE SUR LA SOURCE : une date écrite dans le markdown (`valide:AAAA-MM-JJ`)
    est un fait connu — fin d'un dispositif, échéance d'un arrêté —, alors que la cadence de
    la source n'est qu'un rythme de surveillance par défaut.

    Une date mal écrite est ignorée et signalée, jamais devinée : mieux vaut un document sans
    fin de validité qu'une péremption inventée à partir d'une faute de frappe.
    """
    brut = entry.get("valide_brut")
    if brut:
        try:
            return date.fromisoformat(brut), None
        except ValueError:
            return None, f"« {entry['titre']} » : valide:{brut} n'est pas une date AAAA-MM-JJ, ignorée"
    if source.validite_mois:
        return _ajoute_mois(date_contenu, source.validite_mois), None
    return None, None


async def crawl_source(db: AsyncSession, source: SourceSpec) -> dict:
    """Ingestion/rafraîchissement d'une source dans le RAG. Upsert par (source, titre).

    L'EMPREINTE DÉCIDE DE TOUT (migration 0022). Contenu identique au passage précédent :
    on note le passage et on s'arrête. Deux raisons, dont la seconde est la plus importante :

    - l'embedding est la SEULE opération coûteuse ici (Ollama, en local, sur processeur) —
      ré-embarquer une base entière qui n'a pas bougé, c'est des minutes aujourd'hui et des
      heures le jour où le crawler ramènera des milliers de documents ;
    - et surtout `date_maj` doit rester la date du dernier CHANGEMENT de contenu. Elle était
      remise à aujourd'hui à chaque passage, ce qui remettait du même coup le compteur de la
      veille à zéro : celle-ci ne pouvait STRUCTURELLEMENT rien signaler comme périmé.

    Un document ingéré avant la migration a une empreinte nulle : il est donc ré-embarqué une
    fois, puis plus jamais sans raison.
    """
    try:
        entries = await _fetch_source_entries(source)
    except Exception as exc:  # réseau, parsing… — journalisé, non bloquant
        await _log(db, "crawler", "error", f"{source.name}: {exc}")
        await db.commit()
        return {"source": source.name, "error": str(exc)}

    added = updated = inchanges = 0
    today = date.today()
    for entry in entries:
        empreinte = _empreinte(entry["content"])
        doc = await db.scalar(
            select(KbDocument).where(KbDocument.source == source.name, KbDocument.titre == entry["titre"])
        )
        chunk = await db.scalar(select(KbChunk).where(KbChunk.document_id == doc.id)) if doc else None

        # Rien n'a changé. On vérifie quand même que le chunk est là : un document sans
        # chunk est introuvable par la recherche, donc invisible — il doit être refait.
        if doc is not None and doc.empreinte == empreinte and chunk is not None:
            doc.date_crawl = today
            # La fiabilité et la validité viennent de la DÉCLARATION de la source : les
            # reclasser doit s'appliquer sans avoir à toucher aux fiches elles-mêmes.
            doc.fiabilite = entry.get("fiabilite", source.fiabilite)
            validite, anomalie = _valide_jusqu_au(source, entry, doc.date_maj)
            doc.valide_jusqu_au = validite
            if anomalie:
                await _log(db, "crawler", "metadonnee_invalide", f"{source.name}: {anomalie}")
            inchanges += 1
            continue

        if doc is None:
            doc = KbDocument(source=source.name, titre=entry["titre"], date_maj=today, statut="actif")
            db.add(doc)
            await db.flush()
            added += 1
        else:
            doc.date_maj = today  # ici, et seulement ici : le contenu a réellement changé
            updated += 1

        doc.date_crawl = today
        doc.empreinte = empreinte
        doc.fiabilite = entry.get("fiabilite", source.fiabilite)
        doc.zone = entry.get("zone")
        doc.url = entry.get("url") or doc.url
        validite, anomalie = _valide_jusqu_au(source, entry, doc.date_maj)
        doc.valide_jusqu_au = validite
        if anomalie:
            await _log(db, "crawler", "metadonnee_invalide", f"{source.name}: {anomalie}")

        embedding = await embed(entry["content"])
        if chunk is None:
            db.add(KbChunk(document_id=doc.id, content=entry["content"], embedding=embedding,
                           chunk_metadata=entry["metadata"]))
        else:
            chunk.content = entry["content"]
            chunk.embedding = embedding
            chunk.chunk_metadata = entry["metadata"]

    retires = await _elaguer(db, source, {e["titre"] for e in entries})

    await _log(db, "crawler", "ingest_source",
               f"{source.name}: {added} ajoutés, {updated} mis à jour, {inchanges} inchangés, "
               f"{retires} retirés ({len(entries)} entrées)")
    await db.commit()
    return {"source": source.name, "added": added, "updated": updated,
            "unchanged": inchanges, "removed": retires, "total": len(entries)}


async def run_crawler(db: AsyncSession) -> list[dict]:
    """Parcourt toutes les sources déclarées."""
    return [await crawl_source(db, s) for s in SOURCES]


async def run_veille(db: AsyncSession, max_age_days: int = 180) -> dict:
    """Repère ce qui demande une re-vérification. DEUX signaux, qui ne disent pas la même chose.

    1. VALIDITÉ DÉPASSÉE (`valide_jusqu_au` < aujourd'hui) : une date connue est passée —
       fin d'un dispositif, échéance d'un arrêté, ou la cadence déclarée par la source
       (`SourceSpec.validite_mois`). C'est le signal fort : il y a quelque chose à aller lire.
    2. PAS REVU DEPUIS LONGTEMPS (`date_maj` au-delà du seuil) : le contenu n'a pas bougé
       depuis des mois. Ça ne veut pas dire qu'il est faux, seulement que personne ne l'a
       rouvert. Signal faible, à prendre comme une file d'attente de relecture.

    Un document qui coche les deux n'est compté qu'une fois, dans le premier.

    AVANT LA MIGRATION 0022, RIEN DE TOUT ÇA NE POUVAIT SE DÉCLENCHER : le crawler écrivait
    `date_maj = today` à chaque passage, donc aucun document n'atteignait jamais le seuil.
    Le « 0 document périmé » qu'on lisait dans le journal était la seule réponse possible.

    À savoir en lisant les premiers relevés : pour les fiches déjà en base, `date_maj` porte
    encore la date du dernier crawl, pas celle de leur dernier vrai changement — cette
    information n'existe nulle part et ne peut pas être reconstituée. Le compteur part donc
    de maintenant, et devient exact à mesure que les fiches évoluent.
    """
    aujourdhui = date.today()
    seuil = aujourdhui - timedelta(days=max_age_days)

    expires = list(await db.scalars(
        select(KbDocument).where(
            KbDocument.statut == "actif",
            KbDocument.valide_jusqu_au.is_not(None),
            KbDocument.valide_jusqu_au < aujourdhui,
        )
    ))
    for doc in expires:
        await _log(db, "veille", "validite_depassee",
                   f"Validité dépassée le {doc.valide_jusqu_au} : « {doc.titre} » "
                   f"(source {doc.source}, fiabilité {doc.fiabilite})")

    deja_vus = {d.id for d in expires}
    anciens = [
        d for d in await db.scalars(
            select(KbDocument).where(KbDocument.date_maj < seuil, KbDocument.statut == "actif")
        )
        if d.id not in deja_vus
    ]
    for doc in anciens:
        await _log(db, "veille", "stale_flag",
                   f"À relire : « {doc.titre} » (source {doc.source}, contenu inchangé depuis {doc.date_maj})")

    stale = expires + anciens
    await _log(db, "veille", "run",
               f"{len(expires)} validité(s) dépassée(s), {len(anciens)} document(s) non revu(s) "
               f"depuis {max_age_days} j")
    await db.commit()
    return {"stale": len(stale), "validite_depassee": len(expires), "jamais_revus": len(anciens),
            "seuil_jours": max_age_days, "titres": [d.titre for d in stale[:20]]}
