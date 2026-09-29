"""Simulateur « maison + équipements » — étape 1.

`/calcul` et `/options` sont PUBLICS et sans compte : rien n'est enregistré côté serveur
pour un visiteur anonyme, et la réponse ne renvoie jamais son adresse complète — seulement
la commune et des coordonnées arrondies, celles-là mêmes qui servent au cache PVGIS.

Les anciens points d'entrée (`/api/solar/*`, `/api/autoconso/*`) restent en place et
intacts : ils sont REMPLACÉS dans le parcours, pas supprimés.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.ratelimit import limiter
from app.models.house import House
from app.models.simulateur import SimulateurStudy
from app.models.user import User
from app.schemas.simulateur import EtudeIn, SimulateurIn
from app.services import (
    awg, batterie_virtuelle, eolien, geocoding, simu_climat, simu_conso, simu_engine,
    simu_options, simu_pv,
)
from app.services.geocoding import GeocodingError
from app.services.pvgis import PvgisError
from app.services.simu_types import (
    Clim, Configuration, Eau, Eolien, Lieu, Maison, Panneaux, Piscine, Stockage, Voiture,
)

router = APIRouter(prefix="/simulateur", tags=["simulateur"])


def _vers_configuration(payload: SimulateurIn, lieu: Lieu) -> Configuration:
    """Traduit l'entrée HTTP en objets du domaine. Le moteur ne connaît pas Pydantic."""
    m = payload.maison
    maison = Maison(
        surface_m2=m.surface_m2,
        nb_occupants=m.nb_occupants,
        presence_journee=m.presence_journee,
        residence_secondaire=m.residence_secondaire,
        mois_occupation=tuple(m.mois_occupation),
        chauffage=m.chauffage,
        ecs=m.ecs,
        clim=Clim(present=m.clim.present, deja_installe=m.clim.deja_installe,
                  nb_pieces=m.clim.nb_pieces, plage=m.clim.plage),
        piscine=Piscine(present=m.piscine.present, deja_installe=m.piscine.deja_installe,
                        volume_m3=m.piscine.volume_m3, pompe_kw=m.piscine.pompe_kw),
        voiture=Voiture(present=m.voiture.present, deja_installe=m.voiture.deja_installe,
                        km_an=m.voiture.km_an, recharge=m.voiture.recharge,
                        presente_en_journee=m.voiture.presente_en_journee),
        conso_connue_kwh_an=m.conso_connue_kwh_an,
        puissance_souscrite_kva=m.puissance_souscrite_kva,
        raccordement=m.raccordement,
        besoin_secours=m.besoin_secours,
    )
    p = payload.panneaux
    s = payload.stockage
    if payload.eau.modele and payload.eau.modele not in awg.MODELES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Modele de machine a eau inconnu : {payload.eau.modele}")
    if s.batterie_virtuelle and s.batterie_virtuelle not in batterie_virtuelle.offres():
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Offre de batterie virtuelle inconnue : {s.batterie_virtuelle}")
    return Configuration(
        lieu=lieu,
        maison=maison,
        panneaux=Panneaux(nb_panneaux=p.nb_panneaux, orientation=p.orientation,
                          inclinaison=p.inclinaison, ombrage=p.ombrage,
                          nb_panneaux_carport=p.nb_panneaux_carport,
                          surface_toit_m2=p.surface_toit_m2),
        eolien=Eolien(kwc=payload.eolien.kwc,
                      facteur_anemometre=payload.eolien.facteur_anemometre),
        eau=Eau(modele=payload.eau.modele,
                solaire_uniquement=payload.eau.solaire_uniquement),
        stockage=Stockage(nb_packs=s.nb_packs, inertie=s.inertie,
                          batterie_virtuelle=s.batterie_virtuelle,
                          palier_virtuel_kwh=s.palier_virtuel_kwh, pilotage=s.pilotage),
        hausse_prix_pct_an=payload.hausse_prix_pct_an,
    )


async def _localiser(payload: SimulateurIn) -> Lieu:
    if payload.lat is not None and payload.lon is not None:
        return Lieu(lat=payload.lat, lon=payload.lon, commune=None)
    try:
        geo = await geocoding.geocode(payload.adresse or "")
    except GeocodingError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return Lieu(lat=geo["lat"], lon=geo["lon"], commune=geo.get("commune"))


async def _preparer(payload: SimulateurIn):
    """Localisation + production PVGIS + courbe de consommation — le socle des deux routes."""
    lieu = await _localiser(payload)
    config = _vers_configuration(payload, lieu)
    try:
        production = await simu_pv.production(lieu, config.panneaux)
    except PvgisError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            f"Service de production solaire indisponible : {exc}") from exc
    profil = simu_conso.construire(config.maison)
    return config, profil, production


def _lieu_public(config: Configuration) -> dict:
    """Ce qu'on accepte de renvoyer : la commune et des coordonnées arrondies. Jamais l'adresse."""
    pas = settings.simu_pvgis_pas_grille_deg
    return {
        "commune": config.lieu.commune,
        "lat": round(round(config.lieu.lat / pas) * pas, 4),
        "lon": round(round(config.lieu.lon / pas) * pas, 4),
        "precision_deg": pas,
    }


@router.post("/calcul")
@limiter.limit("120/minute")
async def calcul(request: Request, payload: SimulateurIn):
    """Les indicateurs de la configuration courante. Appelé à chaque changement de réglage."""
    config, profil, production = await _preparer(payload)
    # L'eolienne se calcule ici, pas dans le moteur : elle depend du LIEU, et le moteur
    # ne connait que des series horaires. La station retenue est renvoyee a l'ecran.
    eolien_h, info_vent = eolien.production_horaire(
        config.eolien.kwc, config.lieu.lat, config.lieu.lon, config.eolien.facteur_anemometre)

    # La machine a eau ne declenche l'appel climat QUE si elle est posee : PVGIS renvoie
    # 1,2 Mo pour une annee type, on ne le demande pas pour rien. Ensuite c'est en cache.
    eau_litres_h = eau_kwh_h = None
    if config.eau.modele:
        temperature_h, humidite_h = await simu_climat.climat(
            lat=config.lieu.lat, lon=config.lieu.lon)
        eau_litres_h, eau_kwh_h = awg.horaire(config.eau.modele, temperature_h, humidite_h)

    resultat = simu_engine.calculer(config, profil, production["total_h"], eolien_h=eolien_h,
                                    eau_litres_h=eau_litres_h, eau_kwh_h=eau_kwh_h)
    return {
        "lieu": _lieu_public(config),
        "production": {
            "annuel_kwh": round(production["annuel_kwh"], 1),
            "par_kwc_kwh": round(production["par_kwc_kwh"], 1),
            "kwc_toit": production["kwc_toit"],
            "kwc_carport": production["kwc_carport"],
            "pertes_pct": production["pertes_pct"],
            # L'ecretage et le seuil au-dela duquel il devient un avertissement. L'ecran
            # s'en sert pour en parler EN PETIT tant qu'il est negligeable — plutot que de
            # le taire, ou d'en faire un bandeau rouge pour quelques euros par an.
            "ecrete_kwh": round(resultat["bilan_annuel"]["ecrete"], 1),
            "ecrete_seuil_pct": settings.simu_ecretage_alerte_pct,
            # D'ou vient l'estimation du vent : la station et sa distance, pour que
            # personne ne prenne un profil releve a 200 km pour une mesure locale.
            "vent": info_vent,
        },
        "panneaux_max_toit": simu_pv.panneaux_max_du_toit(payload.panneaux.surface_toit_m2),
        "version_moteur": simu_engine.VERSION_MOTEUR,
        **resultat,
    }


@router.post("/options")
@limiter.limit("30/minute")
async def options(request: Request, payload: SimulateurIn):
    """Les 3 options chiffrées, la prochaine étape et les objectifs.

    Plus coûteux que `/calcul` (des dizaines de passages horaires) : le front ne l'appelle
    qu'à l'ouverture de l'onglet Étude et après un temps d'inactivité, pas à chaque clic.
    """
    config, profil, production = await _preparer(payload)
    return {
        "lieu": _lieu_public(config),
        "version_moteur": simu_engine.VERSION_MOTEUR,
        **simu_options.calculer_options(config, profil, production),
    }


@router.get("/offres")
async def offres():
    """Les offres de batterie virtuelle connues, avec leurs contraintes affichées."""
    return [
        {
            "code": offre.code,
            "label": offre.label,
            "fournisseur_impose": offre.fournisseur_impose,
            "activation_eur": offre.activation_eur,
            "abonnement_par_kwc_mois": offre.abonnement_par_kwc_mois,
            "paliers_kwh": [{"kwh": k, "eur_mois": e} for k, e in sorted(offre.paliers_kwh)],
            "cout_restitution_eur_kwh": offre.cout_restitution_eur_kwh,
            "grille_complete": offre.grille_complete,
            "note": offre.note,
            "conseil": offre.conseil,
            "recommandee": offre.recommandee,
        }
        for offre in batterie_virtuelle.offres().values()
    ]


@router.post("/etudes", status_code=status.HTTP_201_CREATED)
async def enregistrer_etude(
    payload: EtudeIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enregistre une étude. Le résultat est RECALCULÉ côté serveur, jamais repris du client."""
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Créez d'abord votre fiche Maison pour enregistrer une étude.")

    config, profil, production = await _preparer(payload.configuration)
    resultat = simu_engine.calculer(config, profil, production["total_h"])

    etude = SimulateurStudy(
        house_id=house.id,
        nom=payload.nom,
        configuration=payload.configuration.model_dump(mode="json"),
        resultat={"lieu": _lieu_public(config), **resultat},
        version_moteur=simu_engine.VERSION_MOTEUR,
    )
    db.add(etude)
    await db.commit()
    await db.refresh(etude)
    return {"id": etude.id, "nom": etude.nom, "version_moteur": etude.version_moteur,
            "created_at": etude.created_at}


@router.get("/etudes")
async def lister_etudes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    if house is None:
        return []
    rows = await db.scalars(
        select(SimulateurStudy)
        .where(SimulateurStudy.house_id == house.id)
        .order_by(SimulateurStudy.created_at.desc())
    )
    return [
        {
            "id": etude.id,
            "nom": etude.nom,
            "version_moteur": etude.version_moteur,
            "created_at": etude.created_at,
            "configuration": etude.configuration,
            "indicateurs": (etude.resultat or {}).get("indicateurs"),
        }
        for etude in rows
    ]


@router.get("/etudes/{etude_id}")
async def detail_etude(
    etude_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    house = await db.scalar(select(House).where(House.user_id == user.id))
    etude = await db.get(SimulateurStudy, etude_id)
    if etude is None or house is None or etude.house_id != house.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Étude introuvable")
    return {
        "id": etude.id, "nom": etude.nom, "version_moteur": etude.version_moteur,
        "created_at": etude.created_at, "configuration": etude.configuration,
        "resultat": etude.resultat,
    }
