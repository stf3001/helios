"""Point 13 : plus aucune page ni réponse du chat sur la table climatique provisoire d'Hydrolia.

Les études hydriques stockées restent en base (rien n'est supprimé) ; elles ne sont simplement
plus lues ni transmises.
"""

import inspect
from pathlib import Path

from app.main import app
from app.routers import chat
from app.services import rag

RACINE = Path(__file__).resolve().parents[2]


def test_le_chat_ne_charge_ni_n_envoie_l_etude_hydrique():
    assert "WaterStudy" not in inspect.getsource(chat)
    assert not hasattr(rag, "build_water_context")
    assert "water_context" not in inspect.signature(rag.build_user_content).parameters
    contenu = rag.build_user_content("Combien d'eau ?", [], audit_context={"x": 1})
    assert "HYDRIQUE" not in contenu


def test_l_api_water_n_existe_plus():
    assert not [r for r in app.routes if getattr(r, "path", "").startswith("/api/water")]


def test_la_page_redirige_vers_le_simulateur():
    assert "location = /potentiel-hydrique { return 301 /simulateur-solaire; }" in (
        RACINE / "deploy" / "nginx.conf").read_text(encoding="utf-8")
    assert '<Route path="/potentiel-hydrique" element={<Navigate to="/simulateur-solaire" replace />} />' in (
        RACINE / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
