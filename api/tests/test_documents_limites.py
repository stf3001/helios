"""Point 49 : 50 documents et 250 Mo par maison, photos de pièce hors compte — CONTRE LA VRAIE BASE.

Même dispositif que `test_carnet_api.py` (sauté sans base). Le plafond en octets est testé en
l'abaissant le temps du test : écrire 250 Mo de fichiers n'apprendrait rien de plus.
"""

import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import async_session, engine
from app.core.security import create_access_token
from app.main import app
from app.models.house import House
from app.models.piece import Piece
from app.models.user import User
from app.routers import documents

PDF = b"%PDF-1.4 test"


async def _base_prete() -> bool:
    await engine.dispose()  # voir `test_carnet_api._base_prete`
    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1 FROM house_documents LIMIT 1"))
        return True
    except Exception:
        return False


async def _creer_foyer() -> tuple[uuid.UUID, uuid.UUID]:
    async with async_session() as s:
        user = User(email=f"docs-{uuid.uuid4().hex[:10]}@test.invalid", password_hash="x")
        s.add(user)
        await s.flush()
        house = House(user_id=user.id, code_postal="83000")
        s.add(house)
        await s.flush()
        piece = Piece(house_id=house.id, nom="Séjour", type="sejour")
        s.add(piece)
        await s.commit()
        return user.id, piece.id


async def _effacer(uid) -> None:
    async with async_session() as s:
        h = await s.scalar(text("SELECT id FROM houses WHERE user_id = :u"), {"u": uid})
        if h:
            for chemin in await s.scalars(text("SELECT path FROM house_documents WHERE house_id = :h"), {"h": h}):
                Path(chemin).unlink(missing_ok=True)
            await s.execute(text("DELETE FROM house_documents WHERE house_id = :h"), {"h": h})
            await s.execute(text("DELETE FROM houses WHERE id = :h"), {"h": h})
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
        await s.commit()


@pytest.fixture(scope="module")
def foyer():
    with TestClient(app) as client:
        if not client.portal.call(_base_prete):
            pytest.skip("Postgres de développement absent")
        uid, piece_id = client.portal.call(_creer_foyer)
        try:
            yield client, {"Authorization": f"Bearer {create_access_token(str(uid))}"}, piece_id
        finally:
            client.portal.call(lambda: _effacer(uid))
            client.portal.call(engine.dispose)


def _deposer(c, h, nom="f.pdf", **form):
    return c.post("/api/houses/me/documents", headers=h, data={"type": "facture", **form},
                  files={"file": (nom, io.BytesIO(PDF), "application/pdf")})


def test_plafond_total_refuse(foyer, monkeypatch):
    c, h, _ = foyer
    monkeypatch.setattr(documents, "MAX_OCTETS_PAR_MAISON", len(PDF) + 5)
    assert _deposer(c, h).status_code == 201
    r = _deposer(c, h)
    assert r.status_code == 400 and "Mo atteint" in r.json()["detail"]
    # Le document refusé n'a rien laissé : on repart d'un seul document.
    assert len([d for d in c.get("/api/houses/me/documents", headers=h).json() if not d["piece_id"]]) == 1


def test_cinquante_documents_puis_refus_et_photo_hors_compte(foyer):
    c, h, piece_id = foyer
    deja = len([d for d in c.get("/api/houses/me/documents", headers=h).json() if not d["piece_id"]])
    for i in range(deja, documents.MAX_DOCUMENTS_PAR_MAISON):
        assert _deposer(c, h, nom=f"f{i}.pdf").status_code == 201, i
    r = _deposer(c, h)
    assert r.status_code == 400 and "Limite de 50 documents" in r.json()["detail"]
    # La photo d'une pièce reste hors compte, même à la limite.
    r = c.post("/api/houses/me/documents", headers=h, data={"piece_id": str(piece_id)},
               files={"file": ("sejour.png", io.BytesIO(b"\x89PNG test"), "image/png")})
    assert r.status_code == 201, r.text
