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

#: Fuseau de reference. L'equipe appelle depuis la France ; stocker en UTC et afficher
#: en heure locale demanderait une bibliotheque de fuseaux pour un gain nul ici.
FUSEAU = timezone(timedelta(hours=2))


def _heures_du_jour(jour: date) -> list[datetime]:
    """Les debuts de creneau d'une journee, selon la grille d'ouverture."""
    creneaux: list[datetime] = []
    pas = timedelta(minutes=settings.rdv_duree_min)
    for debut_h, fin_h in settings.rdv_plages_horaires:
        moment = datetime.combine(jour, time(hour=int(debut_h), minute=round((debut_h % 1) * 60)),
                                  tzinfo=FUSEAU)
        fin = datetime.combine(jour, time(hour=int(fin_h), minute=round((fin_h % 1) * 60)),
                               tzinfo=FUSEAU)
        while moment + pas <= fin:
            creneaux.append(moment)
            moment += pas
    return creneaux


def proposables(maintenant: datetime | None = None) -> list[datetime]:
    """Tous les creneaux de la grille, du prochain jour ouvre a l'horizon.

    Le delai de prevenance evite de proposer un appel dans dix minutes : personne ne peut
    le tenir, et un creneau non tenu vaut moins que pas de creneau du tout.
    """
    maintenant = maintenant or datetime.now(FUSEAU)
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
    pris = {r.astimezone(FUSEAU) for r in reserves}
    return [c for c in proposables(maintenant) if c not in pris]


def est_proposable(creneau: datetime, maintenant: datetime | None = None) -> bool:
    """Un creneau envoye par le client tombe-t-il bien sur la grille ?

    Sans ce controle, n'importe quelle date passerait : 3 h du matin, un dimanche, ou
    dans six mois. C'est le serveur qui decide de ses heures d'ouverture, pas le client.
    """
    return creneau.astimezone(FUSEAU) in set(proposables(maintenant))
