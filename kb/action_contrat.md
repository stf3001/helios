# Base de connaissances — Adapter son contrat d'électricité à sa maison (source action_contrat)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source action_contrat).
# Fiche « levier gratuit » du pré-audit. Complète faq_maison.md (§12) et achat_energie.md sans les répéter.
# Neutralité : aucun fournisseur n'est recommandé ni nommé ici.

---

### Q: Mon contrat d'électricité est-il adapté à ma maison ?
`cat: energie | tags: contrat, puissance_souscrite, option_tarifaire, pre_audit | verif: generique`
R: Trois vérifications, gratuites et faisables en dix minutes avec votre facture :
1. **La puissance souscrite** (en kVA). Trop haute, vous payez un abonnement inutile chaque mois. Trop basse, le compteur disjoncte quand plusieurs gros appareils tournent ensemble. Le compteur Linky affiche la puissance maximale atteinte : comparez-la à votre abonnement (repères dans notre fiche « Ma puissance souscrite est-elle bien dimensionnée ? »).
2. **L'option tarifaire** (base, heures pleines / heures creuses, Tempo). Les heures creuses ne sont intéressantes que si une bonne part de votre consommation y tombe : ballon d'eau chaude, recharge de voiture, lave-linge programmé.
3. **Le prix du kWh et sa durée.** Si votre prix est bloqué, notez la date de fin : c'est le moment de comparer.
Votre pré-audit repère ce qui ne colle pas avec votre fiche Maison et le signale dans « Maintenant ». Il ne recommande jamais de fournisseur.

### Q: Mon ballon d'eau chaude chauffe-t-il bien aux heures creuses ?
`cat: energie | tags: ballon, heures_creuses, contacteur, verification | verif: generique`
R: Ça se vérifie au tableau électrique. Le ballon est commandé par un **contacteur jour/nuit**, un petit module avec un sélecteur à trois positions : « 0 » (arrêt), « 1 » ou « marche forcée », et « auto ». En position « auto », le ballon ne chauffe que lorsque le compteur passe en heures creuses. S'il est resté sur la marche forcée (après une intervention, une panne, un dépannage « pour voir »), le ballon chauffe aussi en heures pleines, et vous perdez tout l'intérêt de l'option. Avec des panneaux solaires, c'est l'inverse : on cherche à le faire chauffer en journée, sur votre production, avec un pilotage adapté (voir notre fiche sur le pilotage).

### Q: Mon prix bloqué arrive à échéance : que vérifier ?
`cat: energie | tags: prix_bloque, fin_contrat, comparaison | verif: generique`
R: D'abord la date exacte et ce qui se passe après : la plupart des offres basculent automatiquement sur une autre offre du même fournisseur, pas forcément la moins chère. Ensuite, comparez avec le comparateur public et gratuit du médiateur national de l'énergie, qui n'a rien à vendre, en entrant votre consommation réelle (relevée sur vos factures ou votre espace Linky). Enfin, regardez la durée d'engagement et les frais de résiliation : en électricité, un particulier peut changer de fournisseur sans frais ni coupure. Hélios ne touche aucune commission sur ce choix.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/action_contrat.md ».
     Règles de déclenchement à définir au lot 4 avec les champs puissance_souscrite, option_tarifaire,
     tarif_bloque, tarif_bloque_mois_restants, ecs, chauffage_principal. -->

- **puissance_a_verifier** : « Votre abonnement est de {kva} kVA. Vérifiez sur votre compteur la puissance maximale atteinte : si elle reste nettement en dessous, un cran de moins réduit votre abonnement sans rien changer à votre confort. »
- **hphc_ballon** : « Vous êtes en heures creuses avec un ballon électrique : vérifiez au tableau que son contacteur est bien sur « auto ». »
- **base_avec_ballon** : « Vous êtes en option base avec un ballon électrique : les heures creuses peuvent être intéressantes. Comparez avec votre consommation réelle. »
- **tarif_bloque_fin** : « Votre prix bloqué se termine dans {mois} mois : comparez les offres avant la date, avec le comparateur public du médiateur de l'énergie. »
