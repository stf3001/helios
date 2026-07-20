"""Conseil énergie professionnel — adapté au secteur et aux équipements (déterministe).

Helios identifie un client pro (présence d'un ProProfile) et adapte ses conseils :
postes énergivores du métier, pilotage, contrat pro, potentiel de courtage. Ordres de
grandeur ; les chiffres précis viennent d'une étude, jamais du LLM.
"""
from app.models.pro import ProProfile

SECTEUR_LABEL = {
    "boulangerie": "Boulangerie / pâtisserie",
    "restauration": "Restauration",
    "commerce": "Commerce de détail",
    "artisanat": "Artisanat / atelier",
    "bureau": "Bureau / tertiaire",
    "hotellerie": "Hôtellerie",
    "autre": "Professionnel",
}

# Conseils spécifiques par secteur (postes principaux)
_SECTEUR_TIPS = {
    "boulangerie": [
        ("Fours", "Les fours sont votre premier poste. Décalez les cuissons vers les heures creuses quand c'est possible, et étudiez la récupération de chaleur du four pour l'eau chaude ou le chauffage du fournil."),
        ("Froid", "Entretenez régulièrement chambres froides et vitrines réfrigérées (joints, dégivrage, condenseurs propres) : un froid mal entretenu surconsomme fortement."),
        ("Puissance", "Adaptez la puissance souscrite aux pics du fournil : trop haute, vous payez un abonnement inutile ; trop basse, vous risquez des dépassements coûteux."),
    ],
    "restauration": [
        ("Cuisson & froid", "Cuisson et froid dominent votre facture. Regroupez les cuissons, entretenez le froid, et posez des rideaux de nuit sur les meubles réfrigérés."),
        ("Ventilation", "La ventilation de cuisine est énergivore : asservissez-la à l'activité plutôt que de la laisser en continu."),
    ],
    "commerce": [
        ("Éclairage", "Passez en LED avec détection de présence dans les zones peu fréquentées : gros gain, retour rapide."),
        ("Froid", "Fermez et entretenez les meubles réfrigérés ; régulez la climatisation sur des consignes raisonnables."),
    ],
    "hotellerie": [
        ("Eau chaude & chauffage", "L'ECS et le chauffage sont vos gros postes : régulation par chambre, programmation, et solaire thermique à étudier."),
    ],
    "bureau": [
        ("Clim & chauffage", "Régulez finement la climatisation et le chauffage (consignes, programmation hors présence)."),
        ("Veille", "Coupez la veille des équipements informatiques la nuit et le week-end : un gisement souvent négligé."),
    ],
    "artisanat": [
        ("Air comprimé", "Traquez les fuites d'air comprimé : elles peuvent représenter 20 à 30 % de la consommation du réseau."),
        ("Machines", "Programmez le fonctionnement des machines sur les heures creuses quand la production le permet."),
    ],
}

_EQUIP_TIPS = {
    "chambre_froide": ("Chambre froide", "Vérifiez les joints, le dégivrage et la propreté des condenseurs : un entretien régulier réduit nettement la conso."),
    "vitrine_refrigeree": ("Vitrines réfrigérées", "Installez des rideaux ou couvercles de nuit : jusqu'à 30 % d'économie sur ces meubles."),
    "four": ("Four", "Étudiez la récupération de chaleur et l'isolation ; évitez les préchauffages trop longs."),
    "climatisation": ("Climatisation", "Relevez les consignes de 1 °C et entretenez les unités : gains immédiats."),
    "air_comprime": ("Air comprimé", "Chasse aux fuites et baisse de la pression au strict nécessaire."),
    "eclairage_intensif": ("Éclairage", "LED + détection/gradation : le plus rentable en général."),
}


def advice(profile: ProProfile) -> dict:
    """Recommandations adaptées + évaluation du potentiel de courtage pro."""
    recos: list[dict] = []

    for sujet, conseil in _SECTEUR_TIPS.get(profile.secteur or "", []):
        recos.append({"sujet": sujet, "conseil": conseil})
    for eq in profile.equipements or []:
        if eq in _EQUIP_TIPS:
            sujet, conseil = _EQUIP_TIPS[eq]
            recos.append({"sujet": sujet, "conseil": conseil})

    # Conseils transverses pro
    recos.append({"sujet": "Contrat d'énergie", "conseil": "En professionnel, les contrats sont négociables et les volumes plus importants : une étude de courtage a souvent un fort potentiel d'économie."})
    recos.append({"sujet": "Suivi", "conseil": "Un suivi de consommation (télérelevé / gestionnaire d'énergie pro) permet de repérer les dérives et de piloter les gros postes."})

    return {
        "secteur": SECTEUR_LABEL.get(profile.secteur or "autre", "Professionnel"),
        "recommandations": recos,
        "courtage_recommande": True,
        "avertissement": "Conseils indicatifs et indépendants. Les chiffres précis viennent d'une étude ; "
                         "HELIOS ne touche aucune commission sur ce conseil.",
    }
