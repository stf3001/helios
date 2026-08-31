"""Comptes de DEMONSTRATION HELIOS (dev/local uniquement).

Garantit qu'on peut montrer le site sans passer par l'inscription ni aller chercher un
lien de vérification dans les logs :

- `test@helios.fr`      — espace client, avec une fiche maison déjà remplie ;
- `demo@helios.fr`      — même chose + droit back-office (`users.is_admin`) ;
- `partenaire.demo@helios.fr` — espace partenaire (`/partenaire`), entreprise active.

Idempotent : relancer le script remet les comptes dans l'état attendu (mot de passe,
email vérifié, statut) sans créer de doublons. La fiche maison existante n'est jamais
écrasée — elle n'est créée que si elle manque.

    cd api
    .venv/Scripts/python -m scripts.seed_demo      (Windows)
    .venv/bin/python -m scripts.seed_demo          (Linux/macOS)

Ne JAMAIS lancer sur la base de production : les mots de passe sont publics.
"""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import async_session
from app.core.security import hash_password
from app.models.house import House
from app.models.partner import Partner
from app.models.user import User
from app.services.completeness import compute_score

CLIENT_EMAIL = "test@helios.fr"
CLIENT_PASSWORD = "helios1234"
ADMIN_EMAIL = "demo@helios.fr"
ADMIN_PASSWORD = "Helios2026!"
PARTNER_EMAIL = "partenaire.demo@helios.fr"
PARTNER_PASSWORD = "Demo2026!"

# Fiche maison de démonstration : assez remplie pour que le simulateur solaire, le chat
# connecté et le pré-audit aient de la matière (le pré-audit exige 70 % de complétude).
FICHE_DEMO = dict(
    code_postal="13100",
    type_logement="maison",
    statut="proprietaire",
    annee_construction="1989_2000",
    surface_habitable=120,
    nb_niveaux=2,
    nb_occupants=4,
    residence_principale=True,
    isolation_combles="partielle",
    isolation_combles_annee=2005,
    isolation_murs="aucune",
    isolation_plancher="aucune",
    menuiseries="double",
    menuiseries_annee=2010,
    ventilation="VMC_simple",
    dpe_lettre="D",
    dpe_annee=2021,
    chauffage_principal="gaz",
    chauffage_principal_annee=2012,
    chauffage_appoint="bois",
    ecs="ballon_elec",
    ecs_annee=2012,
    clim=False,
    regulation="thermostat",
    conso_elec_kwh_an=4800,
    puissance_souscrite="9",
    option_tarifaire="base",
    objectifs=["reduire_facture", "confort_ete"],
    budget_envisage="15-30k",
    horizon="6-24mois",
    orientation_toiture="sud",
    surface_toit_exploitable=40,
    ombrage="aucun",
    pente=30,
)


async def upsert_user(db, email: str, password: str, prenom: str, is_admin: bool) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, prenom=prenom)
        db.add(user)
    user.password_hash = hash_password(password)
    user.prenom = prenom
    # email_verified forcé : sans ça la connexion est refusée et le lien de vérification
    # part dans les logs de l'API en dev.
    user.email_verified = True
    user.is_admin = is_admin
    user.consent_cgu_at = user.consent_cgu_at or datetime.now(timezone.utc)
    await db.flush()
    return user


async def ensure_fiche(db, user: User) -> str:
    """Crée la fiche maison de démo si l'utilisateur n'en a pas. Ne modifie jamais une fiche
    existante : elle peut contenir le travail de saisie fait pendant les tests."""
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is not None:
        return f"fiche existante conservée ({house.completeness_score:.0f} %)"
    house = House(user_id=user.id, **FICHE_DEMO)
    db.add(house)
    await db.flush()
    house.completeness_score = compute_score(house)
    return f"fiche de démo créée ({house.completeness_score:.0f} %)"


async def upsert_partner(db) -> None:
    partner = await db.scalar(select(Partner).where(Partner.email == PARTNER_EMAIL))
    if partner is None:
        partner = Partner(raison_sociale="Solaire Provence (démo)", email=PARTNER_EMAIL)
        db.add(partner)
    partner.password_hash = hash_password(PARTNER_PASSWORD)
    partner.siret = "81234567800017"
    partner.rge = True
    partner.zones = ["13", "83", "84"]
    partner.metiers = ["pv", "pac", "isolation"]
    partner.statut = "actif"  # le login partenaire refuse tout statut != actif
    partner.charte_signee_at = partner.charte_signee_at or datetime.now(timezone.utc)
    partner.note_moyenne = 4.6
    await db.flush()


async def main() -> None:
    async with async_session() as db:
        client = await upsert_user(db, CLIENT_EMAIL, CLIENT_PASSWORD, "Julien", is_admin=False)
        etat_client = await ensure_fiche(db, client)

        admin = await upsert_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, "Stéphane", is_admin=True)
        etat_admin = await ensure_fiche(db, admin)

        await upsert_partner(db)
        await db.commit()

    print("Comptes de démonstration HELIOS prêts :")
    print(f"  {CLIENT_EMAIL} / {CLIENT_PASSWORD}  — espace client — {etat_client}")
    print(f"  {ADMIN_EMAIL} / {ADMIN_PASSWORD}  — espace client + back-office /admin — {etat_admin}")
    print(f"  {PARTNER_EMAIL} / {PARTNER_PASSWORD}  — espace partenaire /partenaire")


if __name__ == "__main__":
    asyncio.run(main())
