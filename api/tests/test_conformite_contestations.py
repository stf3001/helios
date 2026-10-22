"""Mises en relation, lot 3 : partenaire en règle, et règles de contestation — fonctions pures."""

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from app.services import conformite as cf
from app.services import contestations as ct

AUJ = date(2026, 10, 22)


def doc(type_, fin=None, statut="depose", cree=datetime(2026, 10, 1, tzinfo=timezone.utc)):
    return SimpleNamespace(id=f"{type_}-{fin}-{statut}", type=type_, date_fin=fin, statut=statut, created_at=cree)


EN_REGLE = [doc("kbis"), doc("decennale", date(2027, 6, 30)), doc("rge", date(2027, 3, 31))]


def test_en_regle_avec_tout_et_la_charte_en_vigueur():
    assert cf.en_regle(True, EN_REGLE, "v2", "v2", AUJ)


def test_charte_non_signee_ancienne_ou_absente():
    assert not cf.en_regle(True, EN_REGLE, None, "v2", AUJ)
    assert not cf.en_regle(True, EN_REGLE, "v1", "v2", AUJ)      # nouvelle version : nouvelle signature
    assert not cf.en_regle(True, EN_REGLE, "v2", None, AUJ)      # aucune charte en vigueur : personne


def test_justificatif_expire_manquant_ou_refuse():
    expiree = [doc("kbis"), doc("decennale", date(2026, 10, 21)), doc("rge", date(2027, 3, 31))]
    assert not cf.en_regle(True, expiree, "v2", "v2", AUJ)
    assert cf.etat_justificatifs(True, expiree, AUJ)["decennale"]["etat"] == "expire"
    assert not cf.en_regle(True, EN_REGLE[:2], "v2", "v2", AUJ)  # RGE déclaré mais absent
    assert cf.en_regle(False, EN_REGLE[:2], "v2", "v2", AUJ)     # RGE non déclaré : non requis
    refuse = [doc("kbis", statut="refuse"), *EN_REGLE[1:]]
    assert not cf.en_regle(True, refuse, "v2", "v2", AUJ)
    sans_date = [doc("kbis"), doc("decennale", None)]
    assert cf.etat_justificatifs(False, sans_date, AUJ)["decennale"]["etat"] == "manquant"


def test_le_jour_meme_vaut_encore_et_l_echeance_proche_n_exclut_pas():
    juste = [doc("kbis"), doc("decennale", AUJ)]
    assert cf.en_regle(False, juste, "v2", "v2", AUJ)
    assert cf.etat_justificatifs(False, juste, AUJ)["decennale"]["etat"] == "bientot"


def test_le_depot_le_plus_recent_l_emporte():
    vieux = doc("decennale", date(2026, 1, 1), cree=datetime(2025, 1, 1, tzinfo=timezone.utc))
    neuf = doc("decennale", date(2027, 12, 31), cree=datetime(2026, 10, 20, tzinfo=timezone.utc))
    assert cf.etat_justificatifs(False, [neuf, vieux, doc("kbis")], AUJ)["decennale"]["etat"] == "valide"


def test_kbis_de_moins_de_3_mois():
    assert cf.kbis_recent(AUJ - timedelta(days=90), AUJ)
    assert not cf.kbis_recent(AUJ - timedelta(days=91), AUJ)
    assert not cf.kbis_recent(AUJ + timedelta(days=1), AUJ)
    assert not cf.kbis_recent(None, AUJ)


def test_alertes_de_la_banniere():
    a = cf.alertes(True, [doc("kbis"), doc("decennale", date(2026, 10, 1))], None, "v2", AUJ)
    assert a[0] == "Signez la charte v2 pour recevoir de nouvelles demandes."
    assert any("décennale expiré le 01/10/2026" in x for x in a)
    assert any("Qualification RGE à déposer" in x for x in a)
    assert cf.alertes(True, EN_REGLE, "v2", "v2", AUJ) == []
    assert "relecture" in cf.alertes(False, EN_REGLE, None, None, AUJ)[0]


TRANSMIS = datetime(2026, 10, 15, 10, tzinfo=timezone.utc)
LEAD = SimpleNamespace(type="travaux", consent_client_at=TRANSMIS)


def test_contestation_dans_le_delai_de_7_jours():
    assert ct.refus(LEAD, TRANSMIS + timedelta(days=7), [], "doublon", "Déjà client", None) is None
    r = ct.refus(LEAD, TRANSMIS + timedelta(days=7, seconds=1), [], "doublon", "Déjà client", None)
    assert r == "Le délai de 7 jours pour contester est dépassé."
    assert not ct.peut_contester(LEAD, TRANSMIS + timedelta(days=8), [])
    assert ct.peut_contester(LEAD, TRANSMIS + timedelta(days=1), [])


def test_contestation_motif_commentaire_unicite_type():
    m = TRANSMIS + timedelta(days=1)
    assert ct.refus(LEAD, m, [], "trop_cher", "x", None) == "Motif inconnu."
    assert ct.refus(LEAD, m, [], "doublon", "  ", None) == "Un commentaire est obligatoire."
    assert ct.refus(LEAD, m, ["deja"], "doublon", "x", None) == "Cette demande a déjà été contestée."
    assert not ct.peut_contester(LEAD, m, ["deja"])
    energie = SimpleNamespace(type="energie", consent_client_at=TRANSMIS)
    assert ct.refus(energie, m, [], "doublon", "x", None).startswith("Seule")


def test_injoignable_exige_trois_essais_dates():
    m = datetime(2026, 10, 20, 18, tzinfo=timezone.utc)
    trois = [date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 16)]
    assert ct.refus(LEAD, m, [], "injoignable", "Trois appels sans réponse", trois) is None
    assert "3 essais" in ct.refus(LEAD, m, [], "injoignable", "x", trois[:2])
    avant = [date(2026, 10, 14), *trois[1:]]
    assert "après la transmission" in ct.refus(LEAD, m, [], "injoignable", "x", avant)
    futur = [*trois[:2], date(2026, 10, 21)]
    assert "pas du futur" in ct.refus(LEAD, m, [], "injoignable", "x", futur)
