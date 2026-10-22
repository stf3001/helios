"""Mises en relation, lot 5 : jours ouvrés, question au foyer, écarts, indicateurs — sans base."""

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.services import suivi_foyer as sf
from app.services.creneaux import a_paris


def test_paques_et_feries():
    assert sf.paques(2026) == date(2026, 4, 5) and sf.paques(2027) == date(2027, 3, 28)
    f = sf.feries(2026)
    assert {date(2026, 4, 6), date(2026, 5, 14), date(2026, 5, 25), date(2026, 11, 11)} <= f
    assert len(f) == 11


def test_jours_ouvres_week_end_ferie_et_passage_de_mois():
    assert sf.jours_ouvres_depuis(date(2026, 10, 16), date(2026, 10, 19)) == 1      # ven. → lun.
    assert sf.jours_ouvres_depuis(date(2026, 11, 10), date(2026, 11, 17)) == 4      # le 11 novembre ne compte pas
    assert sf.jours_ouvres_depuis(date(2026, 10, 29), date(2026, 11, 5)) == 5       # 30/10, puis 2 au 5/11
    assert sf.jours_ouvres_depuis(date(2026, 12, 24), date(2027, 1, 4)) == 5        # 25/12 et 1/1 fériés
    assert sf.jours_ouvres_depuis(date(2026, 10, 21), date(2026, 10, 21)) == 0


def lead(**kw):
    champs = dict(id=uuid.uuid4(), house_id=uuid.uuid4(), type="travaux", statut="transmis", contacte_le=None,
                  contact_foyer=None, consent_retire_at=None, declarations_foyer=None, prix_ht=60, facturable=True,
                  consent_client_at=a_paris(2026, 10, 14, 10))
    champs.update(kw)
    return SimpleNamespace(**champs)


def test_la_question_n_apparait_qu_apres_5_jours_ouvres_sans_contact():
    l = lead()  # mercredi 14/10
    assert not sf.question_contact_due(l, date(2026, 10, 20))   # 4 jours ouvrés
    assert sf.question_contact_due(l, date(2026, 10, 21))       # 5
    assert not sf.question_contact_due(lead(contacte_le=date(2026, 10, 15)), date(2026, 10, 30))
    assert not sf.question_contact_due(lead(statut="devis"), date(2026, 10, 30))
    assert not sf.question_contact_due(lead(contact_foyer="non"), date(2026, 10, 30))
    assert not sf.question_contact_due(lead(consent_retire_at=datetime.now(timezone.utc)), date(2026, 10, 30))
    assert not sf.question_contact_due(lead(type="energie"), date(2026, 10, 30))


def test_ecarts_seulement_quand_les_deux_se_contredisent():
    assert sf.ecarts(lead(contact_foyer="non", contacte_le=date(2026, 10, 15)))[0]["sujet"] == "contact"
    assert sf.ecarts(lead(contact_foyer="non")) == []                    # le partenaire n'a rien dit
    assert sf.ecarts(lead(contacte_le=date(2026, 10, 15))) == []          # le foyer n'a rien dit
    signe = [{"type": "travaux_signes", "le": "2026-10-20"}]
    assert sf.ecarts(lead(statut="perdu", declarations_foyer=signe))[0]["partenaire"] == "Sans suite"
    abandon = [{"type": "projet_abandonne", "le": "2026-10-20"}]
    assert sf.ecarts(lead(statut="signe", declarations_foyer=abandon))[0]["foyer"] == "Projet abandonné"
    assert sf.ecarts(lead(statut="signe", declarations_foyer=signe)) == []


def test_etape_vue_du_foyer():
    assert sf.etape(lead()) == "transmise"
    assert sf.etape(lead(contact_foyer="oui")) == "contactee"
    assert sf.etape(lead(statut="devis")) == "devis"
    assert sf.etape(lead(declarations_foyer=[{"type": "travaux_signes", "le": "x"}])) == "signee"


def test_indicateurs_et_leurs_sources():
    m1, m2 = uuid.uuid4(), uuid.uuid4()
    a = lead(house_id=m1, contacte_le=date(2026, 10, 16), statut="signe",
             declarations_foyer=[{"type": "travaux_signes", "le": "x"}])
    b = lead(house_id=m1, contact_foyer="non", facturable=False)
    c = lead(house_id=uuid.uuid4(), statut="devis", contacte_le=date(2026, 10, 18))
    d = lead(consent_client_at=a_paris(2026, 9, 3, 10))
    conts = [SimpleNamespace(lead_id=b.id, statut="acceptee"), SimpleNamespace(lead_id=c.id, statut="en_attente")]
    ind = {i["cle"]: i for i in sf.indicateurs([a, b, c, d], conts, {m1, m2}, {a.id: 4, d.id: 2}, "2026-10")}
    assert ind["transmises"]["valeur"] == 3
    assert ind["foyers_etude"]["valeur"] == 50.0 and ind["foyers_etude"]["source"] == "calculé"
    assert ind["delai_contact"]["valeur"] == 3.0 and ind["delai_contact"]["source"] == "déclaré partenaire"
    assert ind["non_contacte"]["numerateur"] == 1 and ind["non_contacte"]["source"] == "déclaré foyer"
    assert (ind["contestation"]["valeur"], ind["acceptation"]["valeur"]) == (66.7, 50.0)
    assert ind["signature_partenaire"]["numerateur"] == 1 and ind["devis_partenaire"]["numerateur"] == 2
    assert ind["signature_foyer"]["numerateur"] == 1
    assert ind["note"]["valeur"] == 4.0
    assert ind["total_ht"]["valeur"] == 60.0   # b acceptée, c en attente : seule a compte
    cumul = {i["cle"]: i for i in sf.indicateurs([a, b, c, d], conts, {m1, m2}, {a.id: 4, d.id: 2})}
    assert cumul["transmises"]["valeur"] == 4 and cumul["note"]["valeur"] == 3.0
