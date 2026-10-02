"""RAG au runtime — doc 07 §4 : recherche, seuil de pertinence, prompt avec constitution."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.house import House
from app.models.kb import KbChunk, KbDocument
from app.services.agents_engine import SOURCES_QR as _QR_SOURCES
from app.services.completeness import _is_filled, compute_score, niveau_for_score

# Version de constitution pilotée par la config (settings.constitution_version) — synchro avec le doc 03.
# Public (pas de underscore) : identique à CHAQUE appel API, quel que soit l'utilisateur ou la question —
# c'est le préfixe envoyé séparément en `system` avec `cache_control` (mise en cache des prompts Anthropic,
# router_llm.py / anthropic_client.py), pour que ce contenu strictement stable soit mis en cache côté API.
_CONSTITUTION_PATH = Path(__file__).resolve().parents[3] / "prompts" / f"constitution-{settings.constitution_version}.md"
constitution_text = _CONSTITUTION_PATH.read_text(encoding="utf-8") if _CONSTITUTION_PATH.exists() else ""


async def search_chunks(db: AsyncSession, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
    distance = KbChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(KbChunk, KbDocument, distance.label("distance"))
        .join(KbDocument, KbChunk.document_id == KbDocument.id)
        .where(KbDocument.statut != "obsolete")
        .order_by(distance)
        .limit(top_k or settings.rag_top_k)
    )
    rows = (await db.execute(stmt)).all()
    return [{"chunk": chunk, "document": document, "score": 1 - dist} for chunk, document, dist in rows]


def best_score(results: list[dict]) -> float:
    return max((r["score"] for r in results), default=0.0)


# Sources dont les chunks sont des fiches Q/R servables telles quelles : `_QR_SOURCES`,
# importee en tete, est declaree une seule fois a cote de SOURCES (services/agents_engine).


#: Seuil de la reponse instantanee quand la question a ete ENRICHIE (relance courte, dont on
#: a devine le sujet d'apres le tour precedent). Plus haut que le seuil normal (0,66), et
#: c'est la seule precaution que demande l'enrichissement.
#:
#: Pourquoi : servir une fiche telle quelle, sans modele, est l'action la plus engageante du
#: chat — il n'y a personne pour rattraper une erreur de recherche. Or sur une relance, le
#: sujet n'est pas celui que le visiteur a ecrit, c'est celui qu'on a suppose. Mesure du
#: 01/10/2026 : « et mes panneaux solaires ? », posee apres une question sur le puits
#: canadien, remontait la fiche du PUITS a 0,661 — juste au-dessus du seuil normal. Helios
#: aurait servi une reponse sur le puits canadien a quelqu'un qui parlait de panneaux.
#:
#: A 0,70, ce cas repasse au modele (qui voit les huit meilleures fiches et peut corriger),
#: tandis que les bonnes relances mesurees — cout 0,739, permis 0,708, hiver 0,731,
#: batterie 0,709, entretien 0,786 — gardent leur reponse instantanee.
RELANCE_INSTANT_MIN = 0.70


def instant_answer(results: list[dict], relance: bool = False) -> str | None:
    """Réponse instantanée sans LLM (doc 07 §5) : si la meilleure fiche Q/R matche
    quasi exactement la question, on sert sa réponse telle quelle — latence nulle,
    zéro risque d'hallucination. Sinon None → parcours LLM normal.

    `relance` : la question a été enrichie du tour précédent pour la recherche. Le sujet
    étant alors supposé et non écrit, on exige davantage de certitude (`RELANCE_INSTANT_MIN`).
    """
    if not results:
        return None
    best = results[0]
    seuil = RELANCE_INSTANT_MIN if relance else settings.rag_instant_answer_threshold
    if best["score"] < seuil:
        return None
    if best["document"].source not in _QR_SOURCES:
        return None
    content = best["chunk"].content
    marker = "\nR:"
    idx = content.find(marker)
    if idx == -1:
        return None
    return content[idx + len(marker):].strip()


def build_partenaires_context(par_metier: dict[str, list[str]], departement: str | None) -> str:
    """Le bloc « annuaire » du prompt : qui couvre la zone de CE visiteur.

    POURQUOI UN BLOC ET PAS UN OUTIL : le modèle local est petit, et un appel de fonction
    qu'il devrait décider lui-même serait raté une fois sur deux. Les noms qui le
    concernent sont donc posés dans le prompt, déjà filtrés par département — il n'a plus
    qu'à les lire.

    LA RÈGLE DE LA CHARTE VIT DANS LE BLOC, pas ailleurs : « ne propose jamais un
    partenaire sans qu'on te le demande » doit être à côté des noms. Enterrée dans la
    constitution, elle est perdue de vue au moment précis où elle compte.
    """
    regle = (
        "RÈGLE ABSOLUE : tu ne cites ces entreprises QUE si le visiteur demande un "
        "professionnel, un installateur, un artisan ou un devis. Jamais de toi-même, "
        "jamais pour appuyer un conseil. Quand tu en cites, donne-les TOUTES pour le "
        "métier concerné — le visiteur choisit, tu ne recommandes pas l'une d'elles."
    )
    if departement is None or not par_metier:
        return (
            "ANNUAIRE DES PARTENAIRES : tu ne sais pas encore où habite ce visiteur. "
            "S'il demande un professionnel, demande-lui d'abord son code postal — "
            "l'annuaire est organisé par département.\n" + regle
        )
    lignes = "\n".join(
        f"- {metier} : {', '.join(noms)}" for metier, noms in sorted(par_metier.items())
    )
    return (
        f"ANNUAIRE DES PARTENAIRES couvrant le département {departement} de ce visiteur :\n"
        f"{lignes}\n{regle}"
    )


#: Nombre d'echanges (question + reponse) relus dans le prompt.
#:
#: Trois, et pas davantage. Ce qu'on cherche a reparer, c'est la relance — « et pour une
#: maison de 1970 ? », « tu m'as dit 6 kWc », « oui vas-y » — qui se joue sur un ou deux
#: tours. Au-dela, on allonge le prompt sans rien gagner, et le modele LOCAL (3B) suit deja
#: mal un prompt de 16 Ko : le journal du projet garde la trace d'un essai de juillet 2026 ou
#: il confondait la fiche du foyer avec un cas pratique fictif. La borne est donc un
#: garde-fou, pas un reglage a monter « pour voir ».
HISTORIQUE_ECHANGES = 3

#: Troncature d'une reponse d'Helios relue. On garde CE QU'IL A DIT, pas la facon dont il
#: l'a dit : les reponses font souvent 1 500 caracteres, dont l'essentiel tient dans les 400
#: premiers. Les questions du visiteur, elles, sont gardees entieres — elles sont courtes,
#: deja bornees a 2 000 caracteres par le schema, et ce sont elles qui portent le contexte.
HISTORIQUE_REPONSE_MAX = 400

#: En deca de cette longueur, une question est presque toujours une RELANCE : « et dans le
#: nord ? », « combien ca coute ? », « pourquoi ? ». Elle ne nomme pas son sujet, donc le
#: vecteur de la recherche n'a rien a quoi se raccrocher et la bonne fiche passe sous le
#: seuil. Mesure du 01/10/2026 : « est-ce que ca marche dans le nord de la France », posee
#: apres une question sur le puits canadien, tombait a 0,485 pour un seuil a 0,50.
#:
#: Une longueur, et rien de plus savant : une question longue porte son sujet toute seule.
#: Le seuil se verifie par la mesure, une detection grammaticale ne se verifierait pas.
RELANCE_MAX_CARACTERES = 45


def build_historique_context(precedents: list) -> str | None:
    """Les derniers tours de la conversation, en un bloc de texte.

    POURQUOI UN BLOC DE TEXTE ET PAS UN VRAI TABLEAU DE MESSAGES : il y a deux chemins de
    generation, l'API Claude et le modele local Ollama, et Ollama n'expose pas de notion de
    conversation (`generate`, pas `chat`). Un seul bloc marche sur les deux, et laisse
    intacte la mise en cache du prefixe `system` cote Anthropic, qui est delicate.

    `precedents` est dans l'ordre chronologique, SANS le message courant.
    """
    if not precedents:
        return None

    lignes = []
    for m in precedents:
        if m.role == "user":
            lignes.append(f"Visiteur : {m.content}")
        else:
            texte = m.content.strip()
            if len(texte) > HISTORIQUE_REPONSE_MAX:
                texte = texte[:HISTORIQUE_REPONSE_MAX].rstrip() + " […]"
            lignes.append(f"Toi (Helios) : {texte}")

    return (
        "CONVERSATION EN COURS — ce qui a deja ete dit, du plus ancien au plus recent.\n"
        + "\n".join(lignes)
        + "\nLe visiteur peut s'y referer sans le repeter (« et pour une maison de 1970 ? », "
        "« tu m'as dit… », « oui vas-y »). Ne lui redemande pas ce qu'il vient de te donner, "
        "et ne recommence pas une reponse deja faite — enchaine."
    )


def question_pour_recherche(question: str, precedents: list) -> str:
    """La question telle qu'on la VECTORISE, qui n'est pas toujours celle qu'on affiche.

    Une relance courte ne nomme pas son sujet : on lui recolle la question precedente du
    visiteur avant de chercher. « et ca marche dans le nord ? » devient « un puits canadien
    marche-t-il partout en France ? et ca marche dans le nord ? », et la recherche retrouve
    de quoi on parle.

    DEUX questions precedentes, pas une. Trouve en testant une vraie conversation le
    02/10/2026 : « c'est quoi un puits canadien », puis « et ca marche dans le nord ? », puis
    « combien ca coute ? ». Avec une seule, le troisieme tour se faisait recoller le
    deuxieme — qui etait lui-meme une relance et ne nommait pas le sujet. Le puits canadien
    disparaissait de la recherche des le troisieme tour. Deux questions l'ancrent.

    Ce qui est renvoye ne sert QU'A la recherche. La question affichee, enregistree en base
    et posee au modele reste celle que le visiteur a ecrite.
    """
    if len(question.strip()) >= RELANCE_MAX_CARACTERES:
        return question
    precedentes = [m.content for m in precedents if m.role == "user"][-2:]
    return " ".join([*precedentes, question]) if precedentes else question


def build_citations(results: list[dict]) -> list[dict]:
    if not results or best_score(results) < settings.rag_score_threshold:
        return []
    return [
        {
            "titre": r["document"].titre,
            "cat": r["chunk"].chunk_metadata.get("cat"),
            "score": round(r["score"], 3),
        }
        for r in results
    ]


# Champs exclus du contexte envoyé au LLM externe (doc 10 sécurité : anonymiser la fiche,
# jamais nom/email, PDL exclu des prompts). `pdl` est une donnée personnelle sensible
# (identifiant de compteur) qui n'apporte rien au conseil : on ne l'envoie jamais au modèle.
_HOUSE_CONTEXT_EXCLUDE = {
    "id", "user_id", "completeness_score", "updated_at",
    "pdl",  # confidentialité (doc 10)
}


def build_house_context(house: House) -> dict:
    """Contexte fiche Maison pour le mode connecté (doc 03 §7) — uniquement les champs renseignés,
    hors données personnelles sensibles (PDL exclu, doc 10 sécurité).

    NB : ne contient pas encore le "dernier audit" mentionné au doc 03 §7 — le
    moteur de pré-audit n'existe pas avant le jalon 6. Point d'extension futur.
    """
    profil = {
        c.name: getattr(house, c.name)
        for c in house.__table__.columns
        if c.name not in _HOUSE_CONTEXT_EXCLUDE and _is_filled(getattr(house, c.name))
    }
    score = compute_score(house)
    return {"score": score, "niveau": niveau_for_score(score), "profil": profil}


def build_pro_context(profile) -> dict:
    """Contexte professionnel pour le chat — Helios détecte un client pro et adapte ses conseils."""
    return {
        "raison_sociale": profile.raison_sociale,
        "secteur": profile.secteur,
        "surface_m2": profile.surface_m2,
        "effectif": profile.effectif,
        "equipements": profile.equipements or [],
        "conso_annuelle_kwh": profile.conso_annuelle_kwh,
        "puissance_kva": profile.puissance_kva,
        "fournisseur_actuel": profile.fournisseur_actuel,
        "contrat_actuel": profile.contrat_actuel,
    }


def build_autoconso_context(study) -> dict:
    """Résumé de la dernière simulation Autoconso (PV/batterie/tarifs) du foyer, pour le contexte
    du chat — Helios peut s'appuyer sur un calcul déjà fait plutôt que de le réinventer."""
    lignes = study.result.get("lignes", [])
    meilleure = max(lignes, key=lambda l: l.get("economie_vs_actuel_eur", 0), default=None)
    return {
        "date_simulation": study.created_at.isoformat() if hasattr(study.created_at, "isoformat") else str(study.created_at),
        "power_kwc": study.params.get("power_kwc"),
        "batterie_kwh": study.params.get("battery_kwh"),
        "mylight_simule": study.params.get("mylight", False),
        "meilleur_scenario": meilleure,
    }


def build_simulation_context(etude) -> dict:
    """Résumé de la dernière étude du simulateur « maison + équipements » du foyer.

    Helios doit repartir de CE calcul plutôt que d'en refaire un de tête. La version du
    moteur est transmise : une étude ancienne repose sur des tarifs qui ont pu changer.
    """
    indicateurs = (etude.resultat or {}).get("indicateurs", {})
    investissement = (etude.resultat or {}).get("investissement", {})
    return {
        "date_simulation": etude.created_at.isoformat()
        if hasattr(etude.created_at, "isoformat") else str(etude.created_at),
        "version_moteur": etude.version_moteur,
        "nom": etude.nom,
        "puissance_kwc": indicateurs.get("puissance_kwc"),
        "autonomie_pct": indicateurs.get("autonomie_pct"),
        "facture_mois_eur": indicateurs.get("facture_mois_eur"),
        "economie_1re_annee_eur": indicateurs.get("economie_1re_annee_eur"),
        "gain_net_25_ans_eur": indicateurs.get("gain_net_25_ans_eur"),
        "temps_retour_ans": indicateurs.get("temps_retour_ans"),
        "investissement_eur": investissement.get("total_eur"),
        "tva_pct": investissement.get("tva_pct"),
        "consommation_estimee": indicateurs.get("conso_estimee"),
    }


def build_solar_context(study) -> dict:
    """Résumé de la dernière étude solaire (PVGIS + scénarios, par puissance 3/6/9 kWc) du foyer —
    évite de renvoyer Helios sur des généralités photovoltaïques quand un calcul chiffré existe déjà."""
    return {
        "date_simulation": study.created_at.isoformat() if hasattr(study.created_at, "isoformat") else str(study.created_at),
        "toiture": {k: v for k, v in study.params.items() if k != "gps"},
        "scenarios_par_puissance": study.scenarios,
    }


def build_audit_context(audit) -> dict:
    """Résumé du dernier pré-audit déterministe du foyer (déperditions, priorités chiffrées) —
    Helios doit s'appuyer sur ce diagnostic déjà fait plutôt que de re-décrire la méthode en général."""
    return {
        "date_audit": audit.created_at.isoformat() if hasattr(audit.created_at, "isoformat") else str(audit.created_at),
        "resultat": audit.json_result,
    }


def build_energy_context(study) -> dict:
    """Résumé de la dernière étude énergie (SOBRY/courtage) du foyer, avec l'avis Helios déjà rendu."""
    return {
        "date_etude": study.created_at.isoformat() if hasattr(study.created_at, "isoformat") else str(study.created_at),
        "type": study.type,
        "statut": study.status,
        "resultat": study.result,
        "avis_helios": study.helios_opinion,
    }


def build_water_context(study) -> dict:
    """Résumé de la dernière étude de potentiel hydrique (Hydrolia) du foyer."""
    return {
        "date_simulation": study.created_at.isoformat() if hasattr(study.created_at, "isoformat") else str(study.created_at),
        "ville": study.params.get("ville"),
        "resultat": study.result,
    }


def build_user_content(
    question: str,
    results: list[dict],
    house_context: dict | None = None,
    pro_context: dict | None = None,
    autoconso_context: dict | None = None,
    solar_context: dict | None = None,
    audit_context: dict | None = None,
    energy_context: dict | None = None,
    water_context: dict | None = None,
    simulation_context: dict | None = None,
    partenaires_context: str | None = None,
    historique_context: str | None = None,
) -> str:
    """Tout ce qui est variable d'une question à l'autre (sources RAG, fiche foyer, études,
    question) — sans la constitution, envoyée séparément en `system` côté API (mise en cache,
    cf. `anthropic_client.generate_stream`). Utilisé seul pour le message utilisateur de l'API,
    et concaténé à la constitution par `build_prompt` pour le modèle local (Ollama, pas de
    séparation system/user ni de cache)."""
    if not results or best_score(results) < settings.rag_score_threshold:
        sources_block = (
            "Aucune source fiable trouvée dans la base de connaissances pour cette question. "
            "Réponds prudemment, sans inventer de chiffre ni de règle."
        )
    else:
        sources_block = "\n\n".join(f"[Source {i + 1}] {r['chunk'].content}" for i, r in enumerate(results))

    if pro_context is not None:
        # Le contexte pro prime : Helios s'adresse à un professionnel et adapte questions/conseils.
        mode_block = (
            "MODE CONNECTÉ — CLIENT PROFESSIONNEL. Profil pro (JSON) :\n"
            f"{json.dumps(pro_context, ensure_ascii=False, default=str)}\n"
            "Adapte tes conseils au métier et aux équipements de ce professionnel (postes énergivores "
            "du secteur, pilotage, contrat pro négociable, potentiel de courtage). Reste franc et indépendant."
        )
        question_label = "Question du client professionnel"
    elif house_context is not None:
        mode_block = (
            "MODE CONNECTÉ — fiche foyer de CE visiteur (JSON, uniquement les champs renseignés) :\n"
            f"{json.dumps(house_context, ensure_ascii=False, default=str)}\n"
            "Adapte ta réponse à ce foyer précis, en te basant sur CES données réelles (pas sur un "
            "exemple de la base de connaissances, même si un « cas pratique » ressemble à sa situation — "
            "les cas pratiques sont des profils fictifs pédagogiques, jamais CE foyer). Si un champ décisif "
            "pour répondre manque, pose la question ou indique quel champ renseigner plutôt que de deviner (doc 03 §4)."
        )
        question_label = "Question de l'utilisateur connecté"
    else:
        mode_block = "MODE PUBLIC (visiteur) — pas de fiche foyer associée."
        question_label = "Question du visiteur"

    # Chaque étude déjà réalisée pour ce foyer est injectée telle quelle : Helios doit s'appuyer
    # sur un calcul déterministe existant plutôt que de rester générique ou d'en réinventer un.
    studies_blocks = []
    for label, ctx in (
        ("DERNIÈRE ÉTUDE SOLAIRE (PVGIS + scénarios)", solar_context),
        ("DERNIER PRÉ-AUDIT ÉNERGÉTIQUE (déperditions + priorités chiffrées)", audit_context),
        ("DERNIÈRE ÉTUDE ÉNERGIE (SOBRY/courtage, avis Helios déjà rendu)", energy_context),
        ("DERNIÈRE SIMULATION AUTOCONSO (PV/batterie/tarifs dynamiques)", autoconso_context),
        ("DERNIÈRE ÉTUDE DE POTENTIEL HYDRIQUE (Hydrolia)", water_context),
        ("DERNIÈRE ÉTUDE DU SIMULATEUR (maison équipée : panneaux, stockage, pilotage)",
         simulation_context),
    ):
        if ctx is not None:
            studies_blocks.append(
                f"{label} DE CE FOYER (JSON) — un calcul déjà fait, réutilise-le plutôt que de "
                f"réinventer des chiffres :\n{json.dumps(ctx, ensure_ascii=False, default=str)}"
            )
    if studies_blocks:
        studies_blocks.append(
            "CONSIGNE : les chiffres (€/an, kWh, %) que tu donnes à CE foyer doivent venir de ces "
            "études ci-dessus, jamais d'une fourchette générale ni d'un « cas pratique » de la base "
            "de connaissances (ce sont des exemples fictifs pour d'autres profils, pas ce foyer)."
        )
    studies_block = ("\n\n---\n" + "\n\n---\n".join(studies_blocks)) if studies_blocks else ""

    # Pose juste avant la question, comme tout ce qui concerne CE visiteur.
    annuaire_block = f"---\n{partenaires_context}\n\n" if partenaires_context else ""

    # EN DERNIER, juste au-dessus de la question : c'est la place qui compte le plus pour un
    # modèle local, et l'historique est ce qui donne son sens à une relance. Plus haut, il
    # serait noyé entre la constitution et les sources.
    historique_block = f"---\n{historique_context}\n\n" if historique_context else ""

    # Ordre volontaire : les modèles locaux (3B) suivent bien mieux ce qui est proche de la question
    # que ce qui est enterré tôt dans un long prompt (constitution + sources) — le profil du foyer et
    # ses études réelles sont donc placés juste avant la question, jamais avant.
    return (
        "SOURCES DISPONIBLES (ne cite que celles fournies ici, jamais d'autres — certaines peuvent être "
        "des cas pratiques fictifs, à but pédagogique uniquement, jamais CE foyer) :\n"
        f"{sources_block}\n\n"
        "---\n"
        f"{mode_block}{studies_block}\n\n"
        f"{annuaire_block}"
        f"{historique_block}"
        "---\n"
        f"{question_label} : {question}\n"
        "Réponse d'Helios :"
    )


def build_prompt(question: str, results: list[dict], *args, **kwargs) -> str:
    """Prompt complet (constitution + contenu variable) pour le modèle local (Ollama), qui n'a
    ni séparation system/user ni mise en cache — voir `build_user_content` pour le détail des
    arguments et le chemin API (constitution envoyée à part, avec `cache_control`)."""
    return f"{constitution_text}\n\n---\n{build_user_content(question, results, *args, **kwargs)}"
