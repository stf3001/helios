r"""Test d'AUTO-RECUPERATION : chaque fiche est interrogee avec sa propre question.

    .venv\Scripts\python.exe -m scripts.test_recall

A QUOI CA SERT, ET POURQUOI CE N'EST PAS LA MEME CHOSE QUE « fiches jamais remontees ».
Le back-office compte les fiches que la recherche n'a jamais fait remonter, mais ce
compteur depend du TRAFIC : avec peu de conversations, il est mathematiquement impossible
que la majorite des fiches remonte, et on avait conclu a tort a un probleme de contenu
(corrige le 27/07/2026). Ici on ne depend pas du trafic : on pose a la base la question
exacte que la fiche pretend traiter. Une fiche qui ne se retrouve pas ELLE-MEME est
introuvable en pratique, quel que soit l'usage.

CE QUE LE TEST REGARDE, EN TROIS QUESTIONS :

1. La fiche se retrouve-t-elle, et a quel rang ? Un rang > 1 veut presque toujours dire
   qu'une autre fiche traite le meme sujet — c'est un detecteur de quasi-doublons. En
   juillet 2026, les 4 fiches releguees etaient toutes des doublons, dont deux qui se
   CONTREDISAIENT sur la batterie virtuelle.
2. Garde-t-elle sa reponse instantanee ? C'est ce qui decide entre ~2 s et une minute, et
   une fiche peut tomber sous le seuil sans que personne ne le voie : la question part au
   modele, qui repond quand meme quelque chose de plausible. Exactement le genre de panne
   qui ne se signale pas.
3. Qui lui prend sa place ? C'est le detail qui dit s'il faut fusionner deux fiches,
   reformuler un intitule, ou ne rien faire.

LE COUT : une question = un embedding local (bge-m3 via Ollama), soit ~1,8 s par fiche sur
le poste de dev. Pour 400 fiches, compter une quinzaine de minutes. Le detail est ecrit en
TSV a cote du resume, pour pouvoir le relire sans tout relancer.

CE QUE LE TEST NE DIT PAS : si la REPONSE est bonne. Il mesure la recherche, pas la
redaction. Une fiche peut se retrouver parfaitement et etre perimee.
"""
import asyncio
import csv
import sys
import time
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session
from app.models.kb import KbChunk, KbDocument
from app.services import ollama_client, rag
from app.services.agents_engine import SOURCES_QR

#: Profondeur de recherche du test, plus large que le `rag_top_k` de production : on veut
#: savoir OU est tombee une fiche reléguée, pas seulement qu'elle a disparu du haut.
PROFONDEUR = 10

SORTIE = Path(__file__).resolve().parent.parent / "generated" / "recall.tsv"


async def mesurer(db, doc: KbDocument, chunk_par_doc: dict) -> dict:
    """Pose a la base la question de cette fiche et regarde ce qui remonte."""
    resultats = await rag.search_chunks(db, await ollama_client.embed(doc.titre), top_k=PROFONDEUR)

    rang = None
    score_propre = None
    for i, r in enumerate(resultats, start=1):
        if r["document"].id == doc.id:
            rang, score_propre = i, r["score"]
            break

    tete = resultats[0] if resultats else None
    # `instant_answer` ne regarde que le PREMIER resultat : une fiche reléguée au rang 2
    # ne sert donc jamais sa reponse telle quelle, meme avec un bon score.
    instant = rag.instant_answer(resultats) is not None

    # L'ÉCART entre le 1er et le 2e : quand deux fiches sans rapport se tiennent à moins de
    # 0,01, aucune n'est « la » réponse, et en servir une telle quelle n'est pas justifié.
    # Mesuré le 13/10/2026 sur de vraies questions de visiteurs : « faut-il une batterie avec
    # des panneaux » servait, instantanément et sans modèle pour la rattraper, une fiche sur
    # les coupures de courant — écart +0,008.
    second = resultats[1] if len(resultats) > 1 else None

    return {
        "titre": doc.titre,
        "source": doc.source,
        "fiabilite": doc.fiabilite,
        "rang": rang or 0,  # 0 = absente des `PROFONDEUR` premiers
        "score_propre": round(score_propre, 4) if score_propre is not None else "",
        "score_tete": round(tete["score"], 4) if tete else "",
        "score_2e": round(second["score"], 4) if second else "",
        "ecart": round(tete["score"] - second["score"], 4) if (tete and second) else "",
        "tete_source": tete["document"].source if tete else "",
        "tete_titre": tete["document"].titre if tete else "",
        "qr": doc.source in SOURCES_QR,
        "instant": instant,
    }


async def main() -> None:
    async with async_session() as db:
        docs = list(await db.scalars(
            select(KbDocument).where(KbDocument.statut == "actif").order_by(KbDocument.source, KbDocument.titre)
        ))
        chunks = {c.document_id: c for c in await db.scalars(select(KbChunk))}
        print(f"{len(docs)} fiches actives, seuil instantane {settings.rag_instant_answer_threshold}, "
              f"seuil de pertinence {settings.rag_score_threshold}\n")

        lignes, t0 = [], time.perf_counter()
        for i, doc in enumerate(docs, start=1):
            lignes.append(await mesurer(db, doc, chunks))
            if i % 25 == 0 or i == len(docs):
                ecoule = time.perf_counter() - t0
                print(f"  {i}/{len(docs)} — {ecoule:.0f} s écoulées, "
                      f"~{ecoule / i * (len(docs) - i):.0f} s restantes", flush=True)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter="\t")
        w.writeheader()
        w.writerows(lignes)

    rapporter(lignes)
    print(f"\nDétail complet : {SORTIE}")


def rapporter(lignes: list[dict]) -> None:
    qr = [l for l in lignes if l["qr"]]
    hors_qr = [l for l in lignes if not l["qr"]]

    rang1 = [l for l in lignes if l["rang"] == 1]
    releguees = [l for l in lignes if l["rang"] > 1]
    introuvables = [l for l in lignes if l["rang"] == 0]

    print("\n=== LA FICHE SE RETROUVE-T-ELLE ? ===")
    print(f"  rang 1      : {len(rang1)}/{len(lignes)}")
    print(f"  reléguée    : {len(releguees)}")
    print(f"  introuvable : {len(introuvables)} (absente des {PROFONDEUR} premiers)")

    # Le sujet du point 28 : une fiche Q/R qui ne sert plus sa reponse telle quelle.
    perdues = [l for l in qr if not l["instant"]]
    seuil = settings.rag_instant_answer_threshold
    sous_seuil = [l for l in perdues if l["rang"] == 1 and l["score_propre"] != "" and l["score_propre"] < seuil]
    volees = [l for l in perdues if l["rang"] != 1]

    print("\n=== GARDE-T-ELLE SA RÉPONSE INSTANTANÉE ? ===")
    print(f"  {len(qr) - len(perdues)}/{len(qr)} fiches Q/R servent leur réponse sans passer par le modèle.")
    print(f"  {len(perdues)} ne le font pas, dont :")
    print(f"    - {len(sous_seuil)} arrivent 1res mais sous le seuil de {seuil}")
    print(f"    - {len(volees)} se font prendre la 1re place par une autre fiche")
    print(f"  ({len(hors_qr)} fiches hors périmètre Q/R, par construction : {sorted({l['source'] for l in hors_qr})})")

    if sous_seuil:
        print(f"\n--- 1res mais sous le seuil (la question part au modèle) ---")
        for l in sorted(sous_seuil, key=lambda x: x["score_propre"]):
            print(f"  {l['score_propre']:.3f}  [{l['source']}] {l['titre'][:88]}")

    if volees:
        print(f"\n--- place prise par une autre fiche (candidats quasi-doublons) ---")
        for l in sorted(volees, key=lambda x: x["rang"], reverse=True):
            print(f"  rang {l['rang']} ({l['score_propre'] or '—'})  [{l['source']}] {l['titre'][:76]}")
            print(f"      devancée par ({l['score_tete']:.3f}) [{l['tete_source']}] {l['tete_titre'][:76]}")

    if introuvables:
        print(f"\n--- INTROUVABLES (le cas grave) ---")
        for l in introuvables:
            print(f"  [{l['source']}] {l['titre'][:88]}")

    # Ce que le point 27 voudra savoir : la fiabilite de ce qui arrive en tete.
    print("\n=== CE QUI ARRIVE EN TÊTE, PAR FIABILITÉ DE LA SOURCE ===")
    par_fiab: dict[str, int] = {}
    for l in lignes:
        par_fiab[l["fiabilite"]] = par_fiab.get(l["fiabilite"], 0) + 1
    for nom, n in sorted(par_fiab.items(), key=lambda kv: -kv[1]):
        print(f"  {nom:14s} {n:4d} fiches interrogées")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
