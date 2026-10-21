"""Les creneaux telephoniques proposables — une grille d'ouverture, rien de plus.

CE QUE CE MODULE N'EST PAS : il ne lit aucun agenda reel. Il propose une grille d'heures
ouvrables, moins les creneaux deja reserves. Tant que les disponibilites des conseillers
ne sont pas branchees, c'est a l'equipe de tenir la promesse : un creneau propose ici
engage quelqu'un a appeler.

Les jours ouvres, les heures et l'horizon sont dans `config.py` — les changer ne demande
pas de toucher a ce fichier.
"""

from datetime import date, datetime, time, timedelta, timezone

from app.core.config import settings

#: L'HEURE DE PARIS, ÉTÉ COMME HIVER. Le module disait +2 en dur : juste en été, décalé d'une
#: heure tout l'hiver (trouvé le 21/10/2026, quatre jours avant le passage à l'heure d'hiver).
#: `zoneinfo` ne trouve pas « Europe/Paris » sous Windows sans le paquet `tzdata` — une
#: dépendance de plus pour une règle qui tient en dix lignes : l'heure d'été européenne va
#: du dernier dimanche de mars au dernier dimanche d'octobre, bascule à 1 h UTC.
_HIVER = timezone(timedelta(hours=1), "CET")
_ETE = timezone(timedelta(hours=2), "CEST")


def _dernier_dimanche(annee: int, mois: int) -> date:
    fin = date(annee, mois, 31)
    return fin - timedelta(days=(fin.weekday() + 1) % 7)


def fuseau_paris(moment) -> timezone:
    """Le décalage de Paris pour un instant (datetime avec fuseau) ou une journée (date)."""
    if isinstance(moment, datetime):
        utc = moment.astimezone(timezone.utc)
        debut = datetime.combine(_dernier_dimanche(utc.year, 3), time(1), tzinfo=timezone.utc)
        fin = datetime.combine(_dernier_dimanche(utc.year, 10), time(1), tzinfo=timezone.utc)
        return _ETE if debut <= utc < fin else _HIVER
    # Une journée : on raisonne à midi, loin des bascules (qui ont lieu la nuit, un dimanche).
    return _ETE if _dernier_dimanche(moment.year, 3) <= moment < _dernier_dimanche(moment.year, 10) else _HIVER


def heure_de_paris(moment: datetime) -> datetime:
    return moment.astimezone(fuseau_paris(moment))


def a_paris(annee: int, mois: int, jour: int, heure: int = 0, minute: int = 0) -> datetime:
    """Une heure « à l'horloge de Paris » ce jour-là (tests, écrans)."""
    j = date(annee, mois, jour)
    return datetime.combine(j, time(heure, minute), tzinfo=fuseau_paris(j))


def _heures_du_jour(jour: date) -> list[datetime]:
    """Les debuts de creneau d'une journee, selon la grille d'ouverture."""
    creneaux: list[datetime] = []
    pas = timedelta(minutes=settings.rdv_duree_min)
    for debut_h, fin_h in settings.rdv_plages_horaires:
        moment = datetime.combine(jour, time(hour=int(debut_h), minute=round((debut_h % 1) * 60)),
                                  tzinfo=fuseau_paris(jour))
        fin = datetime.combine(jour, time(hour=int(fin_h), minute=round((fin_h % 1) * 60)),
                               tzinfo=fuseau_paris(jour))
        while moment + pas <= fin:
            creneaux.append(moment)
            moment += pas
    return creneaux


def proposables(maintenant: datetime | None = None) -> list[datetime]:
    """Tous les creneaux de la grille, du prochain jour ouvre a l'horizon.

    Le delai de prevenance evite de proposer un appel dans dix minutes : personne ne peut
    le tenir, et un creneau non tenu vaut moins que pas de creneau du tout.
    """
    maintenant = heure_de_paris(maintenant or datetime.now(timezone.utc))
    plancher = maintenant + timedelta(hours=settings.rdv_prevenance_h)
    fin = (maintenant + timedelta(days=settings.rdv_horizon_jours)).date()

    creneaux: list[datetime] = []
    jour = maintenant.date()
    while jour <= fin:
        if jour.weekday() in settings.rdv_jours_ouvres:
            creneaux.extend(c for c in _heures_du_jour(jour) if c >= plancher)
        jour += timedelta(days=1)
    return creneaux


def libres(reserves: set[datetime], maintenant: datetime | None = None) -> list[datetime]:
    """La grille moins ce qui est deja pris."""
    pris = {heure_de_paris(r) for r in reserves}
    return [c for c in proposables(maintenant) if c not in pris]


def est_proposable(creneau: datetime, maintenant: datetime | None = None) -> bool:
    """Un creneau envoye par le client tombe-t-il bien sur la grille ?

    Sans ce controle, n'importe quelle date passerait : 3 h du matin, un dimanche, ou
    dans six mois. C'est le serveur qui decide de ses heures d'ouverture, pas le client.
    """
    return heure_de_paris(creneau) in set(proposables(maintenant))
