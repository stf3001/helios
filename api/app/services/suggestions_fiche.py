"""Ce que la fiche Maison sait déjà et que le carnet ne contient pas encore (lot 1).

Une suggestion par champ système renseigné qui n'a pas d'équipement EN SERVICE portant le
même `origine_fiche`. Rien n'est créé ici : le foyer clique, relit le formulaire pré-rempli,
enregistre. Fonction pure — la route lui passe la maison et ses équipements.
"""

# Codes de la fiche (`schemas/house.py`) → types de l'équipement. Ceux qui manquent sont
# repris tels quels (PAC, ballons, VMC : les mêmes codes des deux côtés).
_TYPE_CHAUFFAGE = {
    "elec_direct": "convecteurs", "gaz": "chaudiere_gaz", "fioul": "chaudiere_fioul",
    "bois": "poele_bois", "reseau": "autre",
}
# Une ventilation naturelle, absente ou inconnue n'est pas un appareil qu'on date.
_VENTILATIONS_APPAREIL = ("VMC_simple", "VMC_double")


def suggestions(maison, equipements) -> list[dict]:
    deja = {e.origine_fiche for e in equipements if e.en_service and e.origine_fiche}
    sortie = []

    def ajouter(origine, categorie, valeur_fiche, type_, annee):
        if origine not in deja:
            sortie.append({"origine_fiche": origine, "categorie": categorie, "type": type_,
                           "annee_pose": annee, "valeur_fiche": valeur_fiche})

    for origine in ("chauffage_principal", "chauffage_appoint"):
        valeur = getattr(maison, origine)
        if valeur:
            ajouter(origine, "chauffage", valeur, _TYPE_CHAUFFAGE.get(valeur, valeur),
                    getattr(maison, f"{origine}_annee"))
    if maison.ecs:
        ajouter("ecs", "ecs", maison.ecs, maison.ecs, maison.ecs_annee)
    if maison.clim:
        # La fiche ne dit ni le type (texte libre) ni l'année : au foyer de choisir.
        ajouter("clim", "clim", maison.clim_type or None, None, None)
    if maison.ventilation in _VENTILATIONS_APPAREIL:
        ajouter("ventilation", "ventilation", maison.ventilation, maison.ventilation, None)
    return sortie
