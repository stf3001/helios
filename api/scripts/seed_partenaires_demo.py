"""Partenaires de DÉMONSTRATION pour vérifier les mises en relation (point 60 de TODO.md).

Décision de Stéphane du 22/10/2026 : aucun partenaire réel n'a de charte datée, donc aucun
foyer ne reçoit de proposition. Plutôt que de dater la charte d'un partenaire réel — ce qui
n'appartient qu'à lui —, on crée des partenaires CLAIREMENT FICTIFS :

- nommés « Démo … » ;
- `demo = True` : visibles des seuls comptes de `mer_comptes_demo` (le compte de démo), jamais
  dans l'annuaire public, jamais nommés par le chat, jamais proposés à un autre foyer ;
- charte datée, actifs, dans le Var (83, le département du compte de démo) ;
- le premier a un accès au portail partenaire, pour lire le dossier transmis.

Lot 3 : chacun reçoit des justificatifs « DÉMONSTRATION — sans valeur » (PDF générés ici) et
signe la charte EN VIGUEUR — lancer d'abord `scripts.charger_charte` sur la base de dev. Pour
vérifier l'exclusion, « Démo Combles Provence » a une décennale EXPIRÉE : il sort des
propositions et garde ses demandes.

IDENTIFIANTS DE TEST (base de développement uniquement, comme `demo@helios.fr` dans CLAUDE.md) :
portail partenaire `partenaire-demo@helios.fr`, mot de passe `MOT_DE_PASSE_PORTAIL` ci-dessous.

Idempotent : relancé, il remet les mêmes valeurs. Lancer depuis `api/` :
`.venv/Scripts/python.exe -m scripts.seed_partenaires_demo`
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fpdf import FPDF
from sqlalchemy import delete, select

from app.core.db import async_session
from app.core.security import hash_password
from app.models.partner import Partner, PartnerDocument
from app.services import conformite_lecture, justificatifs

DECENNALE_EXPIREE = "Démo Combles Provence"
LIBELLES = {"kbis": "Extrait Kbis", "decennale": "Attestation d'assurance décennale", "rge": "Qualification RGE"}
EMAIL_PORTAIL = "partenaire-demo@helios.fr"
MOT_DE_PASSE_PORTAIL = "Demo-Partenaire-2026!"

#: raison sociale -> métiers. Quatre partenaires sur les trois mêmes métiers : chacun en a
#: quatre éligibles, donc un vrai tirage de trois.
DEMOS: dict[str, tuple[str, ...]] = {
    "Démo Isolation Azur": ("isolation", "solaire", "pac"),
    "Démo Soleil du Var": ("isolation", "solaire", "pac"),
    "Démo Thermique Maures": ("isolation", "solaire", "pac"),
    "Démo Combles Provence": ("isolation", "solaire", "pac"),
}


def _pdf(nom: str, type_: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "JUSTIFICATIF DE DEMONSTRATION - SANS VALEUR", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, f"{LIBELLES[type_]} - {nom.replace('é', 'e')}", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


async def semer() -> None:
    async with async_session() as db:
        charte = await conformite_lecture.charte_en_vigueur(db)
        if charte is None:
            print("Aucune charte en vigueur : lancer d'abord `scripts.charger_charte` (base de dev).")
        aujourd_hui = date.today()
        for i, (nom, metiers) in enumerate(DEMOS.items()):
            p = await db.scalar(select(Partner).where(Partner.raison_sociale == nom))
            if p is None:
                p = Partner(raison_sociale=nom)
                db.add(p)
            p.demo, p.statut = True, "actif"
            p.zones, p.metiers, p.rge = ["83"], list(metiers), True
            p.lien_interet = None
            p.charte_version_signee = charte.version if charte else None
            p.charte_signee_at = datetime.now(timezone.utc) if charte else None
            if i == 0:
                p.email, p.password_hash = EMAIL_PORTAIL, hash_password(MOT_DE_PASSE_PORTAIL)
            await db.flush()
            for ancien in await db.scalars(select(PartnerDocument).where(PartnerDocument.partner_id == p.id)):
                Path(ancien.path).unlink(missing_ok=True)  # relancé : pas de fichiers orphelins
            await db.execute(delete(PartnerDocument).where(PartnerDocument.partner_id == p.id))
            fin = aujourd_hui + timedelta(days=365)
            for type_, delivrance, date_fin in (
                ("kbis", aujourd_hui - timedelta(days=10), None),
                ("decennale", None, aujourd_hui - timedelta(days=5) if nom == DECENNALE_EXPIREE else fin),
                ("rge", None, aujourd_hui + timedelta(days=20) if i == 1 else fin),  # une échéance proche
            ):
                db.add(justificatifs.ecrire(p, type_, f"{type_}-demo.pdf", "application/pdf", _pdf(nom, type_),
                                            delivrance, date_fin))
        await db.commit()
    print(f"{len(DEMOS)} partenaires de démonstration prêts (visibles du seul compte de démo).")


if __name__ == "__main__":
    asyncio.run(semer())
