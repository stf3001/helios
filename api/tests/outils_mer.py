"""Aides des tests de mises en relation contre la base : mettre un partenaire jetable EN RÈGLE.

Depuis le lot 3, un partenaire n'est proposé que s'il a signé la charte en vigueur et que ses
justificatifs sont valides (`services/conformite.py`). Si aucune charte n'est en vigueur (base
neuve), une version de test est créée puis retirée ; sinon on signe celle qui est là, sans y
toucher. Les justificatifs n'ont pas de fichier : la conformité ne lit que leurs dates.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete

from app.models.partner import Charte, PartnerDocument
from app.services import conformite_lecture


async def assurer_charte(s) -> tuple[str, bool]:
    """(version en vigueur, créée par le test ?)."""
    charte = await conformite_lecture.charte_en_vigueur(s)
    if charte is not None:
        return charte.version, False
    version = f"test-{uuid.uuid4().hex[:8]}"
    s.add(Charte(version=version, texte="Charte de test"))
    await s.flush()
    return version, True


async def retirer_charte(s, version: str, creee: bool) -> None:
    if creee:
        await s.execute(delete(Charte).where(Charte.version == version))


def mettre_en_regle(s, partner, version: str) -> None:
    """À appeler après `flush` (il faut `partner.id`)."""
    partner.charte_version_signee = version
    partner.charte_signee_at = datetime.now(timezone.utc)
    fin = date.today() + timedelta(days=365)
    s.add_all([
        PartnerDocument(partner_id=partner.id, type="kbis", filename="kbis.pdf", path="-",
                        date_delivrance=date.today()),
        PartnerDocument(partner_id=partner.id, type="decennale", filename="decennale.pdf", path="-", date_fin=fin),
        PartnerDocument(partner_id=partner.id, type="rge", filename="rge.pdf", path="-", date_fin=fin),
    ])
