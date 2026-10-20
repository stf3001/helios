# Table d'entretien Hélios — version 1 (20/10/2026)

**Statut : validée le 20/10/2026 par délégation de Stéphane** (points tranchés en section 5 ; relecture complète de Stéphane à venir, toute correction passera par une nouvelle version de ce document). Ce document alimente le lot 3 bis (intégration dans `api/data/entretien/taches.json`).

Règle de lecture : une **obligation** cite un texte officiel ouvert le 20/10/2026 ; une **recommandation** cite un guide public, un fabricant ou l'expertise de Stéphane. Rien n'est inventé : quand aucune source ne donne de fréquence, l'équipement est laissé sans tâche (section 4).

---

## 1. Ce que la table demande au moteur (à ajouter au lot 3 bis)

Le moteur du lot 3 compte en mois depuis la dernière intervention. Les textes sont plus subtils ; il faut cinq ajouts :

| Ajout | Pourquoi | Effet |
|---|---|---|
| `regle: "annee_civile"` + `n_annees` | Chaudière : un entretien **par année civile** ; PAC : **une année civile sur deux**. Fait en mai 2025 → le suivant avant le 31/12/2026, pas avant mai 2026. | Échéance = 31 décembre de (année de la dernière intervention + n). Premier entretien : même calcul depuis la pose. |
| `puissance_kw: {min, max}` | L'obligation PAC et clim ne vise que 4 à 70 kW ; les chaudières, 4 à 400 kW. | Puissance connue hors plage → tâche absente. Puissance inconnue → tâche affichée avec la mention « Obligatoire si la puissance est entre 4 et 70 kW : vérifiez sur la plaque ». |
| `applique_a: {"maison": …}` | Détecteur de fumée et débroussaillement concernent la maison, pas un équipement. | Tâches sans équipement, clé `(tache_id, None)`. |
| Champ de fiche `zone_old` (`oui`, `non`, `ne_sais_pas`) | Le débroussaillement ne vise que les terrains en zone soumise. | `oui` → obligation ; `ne_sais_pas` → une ligne « Vérifiez si votre terrain est concerné » avec le lien Service Public ; `non` → rien. |
| `mois_actifs` | Nettoyer les filtres d'une clim n'a de sens qu'en période d'usage. | Hors de ces mois, la tâche est masquée. |
| `source.type` : `officiel`, `guide`, `fabricant`, `expertise` | Distinguer la loi d'un conseil. | Une obligation exige `officiel`. |

Types à ajouter aux listes du lot 1 s'ils manquent : `chaudiere_bois`, `insert`.

---

## 2. Obligations

| Id | Équipements | Tâche | Fréquence | Qui | Source |
|---|---|---|---|---|---|
| `chaudiere-entretien` | chaudière gaz, fioul, bois (4 à 400 kW) | Entretien par un professionnel qualifié ; attestation remise sous 15 jours, à garder 2 ans | 1 par année civile ; premier au plus tard l'année civile suivant la pose | pro | [Service Public F20760](https://www.service-public.gouv.fr/particuliers/vosdroits/F20760?lang=fr) (vérifiée le 19/05/2025) ; [Code de l'environnement R224-41-4 à R224-41-9](https://www.legifrance.gouv.fr/codes/id/LEGISCTA000020726540) ; [arrêté du 15/09/2009](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000021217854/) |
| `pac-entretien` | PAC air/eau, PAC air/air, clim split, multisplit, gainable (4 à 70 kW) | Entretien par un professionnel (contrôle des parties accessibles, nettoyage, réglages, recherche de fuite) ; attestation sous 15 jours, à garder 2 ans | 1 année civile sur 2 ; premier dans les 2 ans suivant la pose | pro | [Ministère de la Transition écologique](https://www.ecologie.gouv.fr/politiques-publiques/entretien-inspection-systemes-chauffage-climatisation) (Code de l'environnement R224-44 à R224-44-5, décret 2020-912) ; [fiche ADEME, oct. 2023](https://librairie.ademe.fr/ged/8309/fiche-entretien-pompe-chaleur-climatiseur.pdf) |
| `poele-entretien` | poêle bois, poêle à granulés, insert | Entretien de l'appareil par un professionnel | Au moins tous les 12 mois ; premier dans les 12 mois suivant la pose ; dispense si l'appareil n'a pas servi pendant 12 mois (entretien avant de le rallumer) | pro | [Code de la santé publique R1331-68](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047947027/) |
| `ramonage` | poêle bois, poêle à granulés, insert, chaudière fioul, chaudière bois | Ramonage du conduit par une personne qualifiée ; attestation sous 15 jours ouvrés, à garder 2 ans | Au moins tous les 12 mois, de préférence avant la saison de chauffe (septembre-octobre) | pro | [CSP R1331-71](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047947047/) et [R1331-75](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047947083/), en vigueur depuis le 01/10/2023 |
| `spanc-controle` | fosse septique, micro-station | Contrôle périodique par le SPANC (à son initiative) ; garder le rapport, exigé à la vente | Au plus tous les 10 ans, selon la commune | SPANC | [Fiche SPANC de la Métropole Aix-Marseille](https://ampmetropole.fr/wp-content/uploads/2022/08/SPANC-diag-periodique.pdf) (arrêté du 27/04/2012) |
| `debroussaillement` | maison, si `zone_old = oui` | Débroussailler 50 m autour de la maison (100 m si arrêté municipal ou PPRIF), 2 m le long des accès ; tout le terrain en zone U | Maintien permanent ; gros travaux en automne-hiver, entretien au printemps | soi ou pro | [Service Public F33298](https://www.service-public.gouv.fr/particuliers/vosdroits/F33298) (vérifiée le 07/01/2025) ; [arrêté préfectoral du Var du 30/03/2015](https://toulon.fr/sites/new.toulon.fr/files/plaquette_old_var_2015_couleur_16112017.pdf) |

---

## 3. Recommandations

| Id | Équipements | Tâche | Fréquence | Qui | Source |
|---|---|---|---|---|---|
| `detecteur-fumee-test` | maison (tous logements) | Appuyer sur le bouton test ; changer la pile ou l'appareil si besoin | 6 mois, aux changements d'heure (mars, octobre) | soi | Entretien à la charge de l'occupant : [Service Public F19950](https://www.service-public.gouv.fr/particuliers/vosdroits/F19950) (vérifiée le 13/05/2026). La loi ne fixe pas de fréquence : celle-ci est une proposition. |
| `clim-filtres` | PAC air/air, split, multisplit, gainable | Nettoyer les filtres des unités intérieures | 1 mois, en période d'usage (`mois_actifs` : novembre-mars et juin-septembre) | soi | Fiche Hélios `kb/gestes_equipements.md` ; notice du fabricant |
| `pac-unite-exterieure` | PAC air/eau, PAC air/air, clims | Dégager l'unité extérieure (feuilles, végétation, neige), vérifier l'évacuation des condensats | 12 mois, en octobre | soi | Fiche Hélios `kb/gestes_equipements.md` ; notice du fabricant |
| `ballon-groupe-securite` | ballon électrique, ballon thermodynamique | Manœuvrer le levier du groupe de sécurité | 1 mois | soi | [Thermor](https://www.thermor.fr/nos-conseils/detartrage-ballon-eau-chaude) (fabricant) |
| `ballon-detartrage` | ballon électrique, ballon thermodynamique | Détartrer, contrôler l'anode, changer le groupe de sécurité | 24 mois en eau dure (1 à 2 ans), 36 mois en eau douce (2 à 3 ans) | pro ou soi | [Thermor](https://www.thermor.fr/nos-conseils/detartrage-ballon-eau-chaude) (fabricant) |
| `vmc-bouches` | VMC simple flux, double flux | Nettoyer les bouches d'extraction et les entrées d'air | 6 mois | soi | [Fiche « Mon Accompagnateur Rénov' », Ordre des architectes, janv. 2025](https://www.novabuild.fr/wp-content/uploads/2025/02/CNOA-Fiche-MAR-apres-travaux_-fevrier-2025.pdf) |
| `vmc-caisson` | VMC simple flux | Dépoussiérer le caisson | 12 mois | soi ou pro | même fiche |
| `vmc-filtres-double-flux` | VMC double flux | Dépoussiérer ou remplacer les filtres du caisson | 12 mois (la notice peut demander plus souvent) | soi | même fiche ; notice du fabricant |
| `fosse-niveau-boues` | fosse septique | Contrôle visuel du niveau de boues ; vidange par une entreprise agréée quand les boues dépassent la moitié du volume ; nettoyer bac à graisses et préfiltre | 12 mois | soi, vidange par un pro | [Fiche SPANC de la Métropole Aix-Marseille](https://ampmetropole.fr/wp-content/uploads/2022/08/SPANC-diag-periodique.pdf) |
| `micro-station-entretien` | micro-station | Entretien selon le guide d'agrément du fabricant | 12 mois (environ 6 mois pour les micro-stations à boues activées) | pro | même fiche |
| `pv-suivi-production` | panneaux PV, onduleur | Regarder la production du mois dans l'application ; comparer au même mois de l'an passé | 1 mois | soi | Expertise Stéphane, **à valider** |
| `pv-inspection-visuelle` | panneaux PV | Inspection visuelle depuis le sol (salissures, casse, câbles, fixations après un coup de vent) ; ne jamais monter sur le toit | 12 mois, au printemps | soi | Expertise Stéphane, **à valider** |

---

## 4. Équipements laissés sans tâche (aucune source de fréquence fiable)

Batterie, borne de recharge, onduleur (hors suivi de production), adoucisseur, pompe de piscine, éolienne, générateur d'eau atmosphérique, radiateurs à inertie et convecteurs. Ils restent sans rappel jusqu'à ce qu'une notice ou ton expertise donne une fréquence. Pour le générateur d'eau atmosphérique et l'éolienne, la notice GENAQ et les consignes Eolia seront les bonnes sources.

---

## 5. Points tranchés le 20/10/2026

| # | Question | Décision |
|---|---|---|
| 1 | Ramonage d'une chaudière gaz | **Pas de tâche de ramonage pour le gaz.** Une note sur l'entretien annuel rappelle que le chauffagiste contrôle l'évacuation des fumées, et qu'un conduit maçonné raccordé au gaz se ramone selon les règles locales. |
| 2 | Deux ramonages par an pour le bois | **Obligation affichée : une fois par an** (socle national). Une note conseille un second passage en cours de saison quand le bois est le chauffage principal, et rappelle qu'un arrêté local peut l'imposer. |
| 3 | Question `zone_old` | **Posée à toutes les maisons, partout en France** (pas aux appartements), réponse par défaut `ne_sais_pas`, avec le lien vers la fiche Service Public pour vérifier. |
| 4 | Test du détecteur de fumée | **Tous les 6 mois, aux changements d'heure** (mars et octobre). |
| 5 | Détartrage du ballon | **24 mois par défaut**, sans question au foyer pour l'instant (choix prudent : eau dure fréquente dans le Var). |
| 6 | Photovoltaïque | **Les deux recommandations sont gardées** telles quelles. |
| 7 | Contrôle d'étanchéité des fluides | **Compris dans l'entretien PAC**, pas de tâche séparée. |

## 6. JSON prêt pour le lot 3 bis

À recopier tel quel dans `api/data/entretien/taches.json` : toutes les lignes sont validées au 20/10/2026. Les codes de type sont ceux proposés au lot 1 : à aligner sur les codes réellement retenus.

```json
{
  "version": "2026-10-20",
  "avertissement": "Calendrier indicatif. Les obligations citent leur texte ; un arrêté local peut imposer davantage. La notice de votre équipement prime sur les recommandations.",
  "taches": [
    {"id": "chaudiere-entretien", "applique_a": {"categorie": "chauffage", "types": ["chaudiere_gaz", "chaudiere_fioul", "chaudiere_bois"]}, "libelle": "Entretien annuel de la chaudière par un professionnel", "regle": "annee_civile", "n_annees": 1, "puissance_kw": {"min": 4, "max": 400}, "qui": "pro", "nature": "obligation", "mois_preferes": [9, 10], "source": {"type": "officiel", "titre": "Code de l'environnement, art. R224-41-4 à R224-41-9 ; arrêté du 15 septembre 2009", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/F20760"}, "valide_le": "2026-10-20", "note": "Attestation remise sous 15 jours, à conserver 2 ans. Le chauffagiste contrôle l'évacuation des fumées ; un conduit maçonné raccordé au gaz se ramone selon les règles locales."},
    {"id": "pac-entretien", "applique_a": {"categorie": ["chauffage", "clim"], "types": ["PAC_air_eau", "PAC_air_air", "split", "multisplit", "gainable"]}, "libelle": "Entretien de la pompe à chaleur ou de la climatisation par un professionnel", "regle": "annee_civile", "n_annees": 2, "puissance_kw": {"min": 4, "max": 70}, "qui": "pro", "nature": "obligation", "mois_preferes": [9, 10], "source": {"type": "officiel", "titre": "Code de l'environnement, art. R224-44 à R224-44-5 (décret 2020-912)", "url": "https://www.ecologie.gouv.fr/politiques-publiques/entretien-inspection-systemes-chauffage-climatisation"}, "valide_le": "2026-10-20", "note": "Attestation remise sous 15 jours, à conserver 2 ans. Chauffe-eau thermodynamique exclu."},
    {"id": "poele-entretien", "applique_a": {"categorie": "chauffage", "types": ["poele_bois", "poele_granules", "insert"]}, "libelle": "Entretien du poêle ou de l'insert par un professionnel", "regle": "mois", "frequence_mois": 12, "qui": "pro", "nature": "obligation", "mois_preferes": [9, 10], "source": {"type": "officiel", "titre": "Code de la santé publique, art. R1331-68", "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047947027/"}, "valide_le": "2026-10-20", "note": "Dispense si l'appareil n'a pas servi pendant 12 mois ; entretien avant de le rallumer."},
    {"id": "ramonage", "applique_a": {"categorie": "chauffage", "types": ["poele_bois", "poele_granules", "insert", "chaudiere_fioul", "chaudiere_bois"]}, "libelle": "Ramonage du conduit de fumée", "regle": "mois", "frequence_mois": 12, "qui": "pro", "nature": "obligation", "mois_preferes": [9, 10], "source": {"type": "officiel", "titre": "Code de la santé publique, art. R1331-71 et R1331-75", "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000047947047/"}, "valide_le": "2026-10-20", "note": "Attestation sous 15 jours ouvrés, à conserver 2 ans. Si le bois est votre chauffage principal, un second ramonage en cours de saison est conseillé ; un arrêté local peut l'imposer."},
    {"id": "spanc-controle", "applique_a": {"categorie": "eau", "types": ["fosse_septique", "micro_station"]}, "libelle": "Contrôle périodique par le SPANC", "regle": "mois", "frequence_mois": 120, "qui": "pro", "nature": "obligation", "source": {"type": "officiel", "titre": "Arrêté du 27 avril 2012 (contrôle de l'assainissement non collectif)", "url": "https://ampmetropole.fr/wp-content/uploads/2022/08/SPANC-diag-periodique.pdf"}, "valide_le": "2026-10-20", "note": "À l'initiative du SPANC, fréquence fixée par la commune. Garder le rapport : il est exigé à la vente."},
    {"id": "debroussaillement", "applique_a": {"maison": {"zone_old": "oui"}}, "libelle": "Débroussaillement autour de la maison et des accès", "regle": "mois", "frequence_mois": 12, "qui": "soi_ou_pro", "nature": "obligation", "mois_preferes": [11, 12, 1, 2, 3], "source": {"type": "officiel", "titre": "Code forestier, art. L134-5 à L134-18 ; arrêté préfectoral du Var du 30 mars 2015", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/F33298"}, "valide_le": "2026-10-20", "note": "Maintien permanent ; entretien au printemps, jamais en période de sécheresse."},
    {"id": "detecteur-fumee-test", "applique_a": {"maison": {}}, "libelle": "Tester le détecteur de fumée", "regle": "mois", "frequence_mois": 6, "qui": "soi", "nature": "recommande", "mois_preferes": [3, 10], "source": {"type": "officiel", "titre": "Code de la construction et de l'habitation, art. L142-1 à L142-4 et R142-1 à R142-5 (entretien par l'occupant)", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/F19950"}, "valide_le": "2026-10-20", "note": "Fréquence proposée par Hélios : la loi n'en fixe pas."},
    {"id": "clim-filtres", "applique_a": {"categorie": ["chauffage", "clim"], "types": ["PAC_air_air", "split", "multisplit", "gainable"]}, "libelle": "Nettoyer les filtres des unités intérieures", "regle": "mois", "frequence_mois": 1, "mois_actifs": [11, 12, 1, 2, 3, 6, 7, 8, 9], "qui": "soi", "nature": "recommande", "source": {"type": "guide", "titre": "Fiche Hélios « Bien utiliser ses équipements » ; notice du fabricant", "url": null}, "fiche_kb": "gestes_equipements", "valide_le": "2026-10-20"},
    {"id": "pac-unite-exterieure", "applique_a": {"categorie": ["chauffage", "clim"], "types": ["PAC_air_eau", "PAC_air_air", "split", "multisplit", "gainable"]}, "libelle": "Dégager l'unité extérieure et vérifier l'évacuation des condensats", "regle": "mois", "frequence_mois": 12, "qui": "soi", "nature": "recommande", "mois_preferes": [10], "source": {"type": "guide", "titre": "Fiche Hélios « Bien utiliser ses équipements » ; notice du fabricant", "url": null}, "fiche_kb": "gestes_equipements", "valide_le": "2026-10-20"},
    {"id": "ballon-groupe-securite", "applique_a": {"categorie": "ecs", "types": ["ballon_elec", "thermodynamique"]}, "libelle": "Manœuvrer le levier du groupe de sécurité", "regle": "mois", "frequence_mois": 1, "qui": "soi", "nature": "recommande", "source": {"type": "fabricant", "titre": "Thermor, détartrage et entretien du ballon", "url": "https://www.thermor.fr/nos-conseils/detartrage-ballon-eau-chaude"}, "valide_le": "2026-10-20"},
    {"id": "ballon-detartrage", "applique_a": {"categorie": "ecs", "types": ["ballon_elec", "thermodynamique"]}, "libelle": "Détartrer le ballon et contrôler l'anode", "regle": "mois", "frequence_mois": 24, "qui": "soi_ou_pro", "nature": "recommande", "source": {"type": "fabricant", "titre": "Thermor, détartrage et entretien du ballon", "url": "https://www.thermor.fr/nos-conseils/detartrage-ballon-eau-chaude"}, "valide_le": "2026-10-20", "note": "24 mois en eau dure, 36 mois en eau douce."},
    {"id": "vmc-bouches", "applique_a": {"categorie": "ventilation", "types": []}, "libelle": "Nettoyer les bouches et les entrées d'air", "regle": "mois", "frequence_mois": 6, "qui": "soi", "nature": "recommande", "source": {"type": "guide", "titre": "Fiche Mon Accompagnateur Rénov', Ordre des architectes, janvier 2025", "url": "https://www.novabuild.fr/wp-content/uploads/2025/02/CNOA-Fiche-MAR-apres-travaux_-fevrier-2025.pdf"}, "valide_le": "2026-10-20"},
    {"id": "vmc-caisson", "applique_a": {"categorie": "ventilation", "types": ["VMC_simple"]}, "libelle": "Dépoussiérer le caisson de la VMC", "regle": "mois", "frequence_mois": 12, "qui": "soi_ou_pro", "nature": "recommande", "source": {"type": "guide", "titre": "Fiche Mon Accompagnateur Rénov', Ordre des architectes, janvier 2025", "url": "https://www.novabuild.fr/wp-content/uploads/2025/02/CNOA-Fiche-MAR-apres-travaux_-fevrier-2025.pdf"}, "valide_le": "2026-10-20"},
    {"id": "vmc-filtres-double-flux", "applique_a": {"categorie": "ventilation", "types": ["VMC_double"]}, "libelle": "Dépoussiérer ou changer les filtres de la double flux", "regle": "mois", "frequence_mois": 12, "qui": "soi", "nature": "recommande", "source": {"type": "guide", "titre": "Fiche Mon Accompagnateur Rénov', Ordre des architectes, janvier 2025", "url": "https://www.novabuild.fr/wp-content/uploads/2025/02/CNOA-Fiche-MAR-apres-travaux_-fevrier-2025.pdf"}, "valide_le": "2026-10-20", "note": "La notice peut demander plus souvent."},
    {"id": "fosse-niveau-boues", "applique_a": {"categorie": "eau", "types": ["fosse_septique"]}, "libelle": "Contrôler le niveau de boues de la fosse", "regle": "mois", "frequence_mois": 12, "qui": "soi", "nature": "recommande", "source": {"type": "guide", "titre": "SPANC de la Métropole Aix-Marseille-Provence", "url": "https://ampmetropole.fr/wp-content/uploads/2022/08/SPANC-diag-periodique.pdf"}, "valide_le": "2026-10-20", "note": "Vidange par une entreprise agréée quand les boues dépassent la moitié du volume."},
    {"id": "micro-station-entretien", "applique_a": {"categorie": "eau", "types": ["micro_station"]}, "libelle": "Entretien de la micro-station selon son guide d'agrément", "regle": "mois", "frequence_mois": 12, "qui": "pro", "nature": "recommande", "source": {"type": "guide", "titre": "SPANC de la Métropole Aix-Marseille-Provence", "url": "https://ampmetropole.fr/wp-content/uploads/2022/08/SPANC-diag-periodique.pdf"}, "valide_le": "2026-10-20", "note": "Environ tous les 6 mois pour les micro-stations à boues activées."},
    {"id": "pv-suivi-production", "applique_a": {"categorie": "production_electricite", "types": ["panneaux_pv"]}, "libelle": "Regarder la production du mois et la comparer à l'an passé", "regle": "mois", "frequence_mois": 1, "qui": "soi", "nature": "recommande", "source": {"type": "expertise", "titre": "Conseil de Stéphane Aldrighettoni, installateur photovoltaïque", "url": null}, "valide_le": "2026-10-20"},
    {"id": "pv-inspection-visuelle", "applique_a": {"categorie": "production_electricite", "types": ["panneaux_pv"]}, "libelle": "Inspecter les panneaux depuis le sol", "regle": "mois", "frequence_mois": 12, "qui": "soi", "nature": "recommande", "mois_preferes": [4], "source": {"type": "expertise", "titre": "Conseil de Stéphane Aldrighettoni, installateur photovoltaïque", "url": null}, "valide_le": "2026-10-20", "note": "Ne jamais monter sur le toit."}
  ]
}
```

---

## 7. Consigne pour Claude Code (lot 3 bis)

1. Ajouter au moteur les extensions de la section 1, avec leurs tests (année civile, plage de puissance, tâches de maison, `mois_actifs`, type de source). Le champ de fiche `zone_old` s'ajoute par une migration, hors score de complétude, et n'est demandé qu'aux maisons (décision 3).
2. Recopier le JSON de la section 6 tel quel (toutes les lignes portent `valide_le`).
3. Ne modifier aucun libellé, aucune fréquence, aucune source.
4. Vérifier à l'écran le bloc « À faire ce mois-ci » sur trois maisons : chaudière gaz + VMC ; PAC air/eau + ballon thermodynamique + PV ; poêle à bois + fosse septique en zone de débroussaillement.
5. Aucune nouvelle dépendance. Débrief dans `debriefs/`.
