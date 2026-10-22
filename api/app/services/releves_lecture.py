"""Relevés mensuels (lot 4) : ce qui lit et écrit la base autour de `releves` (pur).

- `provisoire` calcule à la demande le relevé d'un mois NON clos, à partir des leads et des
  contestations du moment ;
- `cloturer` fige un mois pour tous les partenaires qui y ont au moins une ligne : instantané
  JSON + PDF, puis plus rien ne les recalcule. Un relevé clos se relit tel quel.
"""
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.house import House
from app.models.partner import Contestation, Lead, Partner, Releve, ReleveCloture
from app.services import releves

PDF_DIR = Path(__file__).resolve().parents[2] / "generated" / "releves"


class ClotureRefusee(Exception):
    pass


async def _donnees(db: AsyncSession, mois: str, partner_id=None):
    """Leads `travaux` à prix fixe transmis dans le mois, leurs contestations et codes postaux."""
    debut, fin = releves.bornes(mois)
    q = (select(Lead, House.code_postal).join(House, House.id == Lead.house_id)
         .where(Lead.type == "travaux", Lead.prix_ht.is_not(None),
                Lead.consent_client_at >= debut, Lead.consent_client_at < fin))
    if partner_id is not None:
        q = q.where(Lead.partner_id == partner_id)
    rows = (await db.execute(q)).all()
    leads = [l for l, _ in rows]
    codes = {l.id: cp for l, cp in rows}
    ids = [l.id for l in leads]
    contests = list(await db.scalars(select(Contestation).where(Contestation.lead_id.in_(ids)))) if ids else []
    return leads, contests, codes


async def cloture(db: AsyncSession, mois: str) -> ReleveCloture | None:
    return await db.get(ReleveCloture, mois)


async def provisoires(db: AsyncSession, mois: str, partner_id=None) -> list[dict]:
    """Un relevé par partenaire qui a au moins une ligne ce mois-là (calculé, non stocké)."""
    leads, contests, codes = await _donnees(db, mois, partner_id)
    pids = {l.partner_id for l in leads}
    partenaires = list(await db.scalars(select(Partner).where(Partner.id.in_(pids)))) if pids else []
    out = []
    for p in sorted(partenaires, key=lambda p: p.raison_sociale):
        r = releves.releve(p, leads, contests, mois, codes)
        r["partenaire"]["demo"] = p.demo
        out.append(r)
    return out


async def releves_du_mois(db: AsyncSession, mois: str, partner_id=None) -> tuple[str, list[dict]]:
    """(« clos » ou « provisoire », relevés). Un mois clos se relit dans ses instantanés."""
    if await cloture(db, mois) is not None:
        q = select(Releve).where(Releve.mois == mois)
        if partner_id is not None:
            q = q.where(Releve.partner_id == partner_id)
        figes = sorted(await db.scalars(q), key=lambda r: r.instantane["partenaire"]["raison_sociale"])
        return "clos", [{**r.instantane, "cloture_le": r.cloture_le.isoformat()} for r in figes]
    return "provisoire", await provisoires(db, mois, partner_id)


async def cloturer(db: AsyncSession, mois: str, par: str, aujourd_hui: date | None = None,
                   pdf=None) -> list[Releve]:
    """Fige le mois. `pdf(instantane, statut) -> bytes` produit le document (injecté pour les tests)."""
    jour = aujourd_hui or date.today()
    if await cloture(db, mois) is not None:
        raise ClotureRefusee(f"Le mois {mois} est déjà clos.")
    possible = releves.cloture_possible_le(mois)
    if jour < possible:
        raise ClotureRefusee(f"Le mois {mois} se clôt au plus tôt le {possible:%d/%m/%Y}, "
                             "après le délai de contestation des demandes de fin de mois.")
    calcules = await provisoires(db, mois)
    attente = [(r["partenaire"]["raison_sociale"], x) for r in calcules for x in r["en_attente"]]
    if attente:
        detail = " ; ".join(f"{nom} — {x['metier']} du {x['date']} ({x['code_postal']})" for nom, x in attente)
        raise ClotureRefusee(f"{len(attente)} contestation(s) encore en attente sur {mois} : {detail}. "
                             "Tranchez-les avant de clore.")
    maintenant = datetime.now(timezone.utc)
    db.add(ReleveCloture(mois=mois, cloture_le=maintenant, cloture_par=par))
    await db.flush()
    figes = []
    for r in calcules:
        r = {**r, "statut": "clos"}
        chemin = None
        if pdf is not None:
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            chemin = PDF_DIR / f"releve-{mois}-{r['partenaire']['id']}.pdf"
            chemin.write_bytes(pdf(r, "clos"))
        rel = Releve(partner_id=r["partenaire"]["id"], mois=mois, instantane=r,
                     pdf_path=str(chemin) if chemin else None, cloture_le=maintenant)
        db.add(rel)
        figes.append(rel)
    await db.commit()
    return figes


async def pdf_du_mois(db: AsyncSession, mois: str, partner_id, rendre) -> tuple[bytes, str]:
    """(contenu, nom) : le PDF FIGÉ d'un mois clos ; sinon un PDF « provisoire » rendu à la demande,
    jamais stocké. `rendre(instantane, statut) -> bytes`. LookupError s'il n'y a pas de relevé."""
    statut, liste = await releves_du_mois(db, mois, partner_id)
    if not liste:
        raise LookupError("Aucun relevé pour ce mois.")
    nom = f"releve-{mois}.pdf"
    if statut == "clos":
        rel = await db.scalar(select(Releve).where(Releve.mois == mois, Releve.partner_id == partner_id))
        if rel is not None and rel.pdf_path and Path(rel.pdf_path).exists():
            return Path(rel.pdf_path).read_bytes(), nom
    return rendre(liste[0], statut), nom
