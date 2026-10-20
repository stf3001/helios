# Base de connaissances — Lire son DPE et le comparer à sa facture (source lire_son_dpe)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source lire_son_dpe).
# Fiche « parcours » du pré-audit : explique le message « réel / théorique » et l'usage du DPE par le moteur.
# Complète faq_maison.md (§8) et reglementation.md (validité du DPE) sans les répéter.

---

### Q: Comment lire mon DPE ?
`cat: dpe | tags: dpe, etiquette, energie_primaire, ges, lecture | verif: reglementation`
R: Un DPE porte deux étiquettes :
- l'**étiquette énergie**, en kWh d'énergie primaire par m² et par an, **tous usages confondus** : chauffage, eau chaude, refroidissement, éclairage et auxiliaires (ventilateurs, pompes) ;
- l'**étiquette climat**, en kg de CO₂ par m² et par an.
La lettre finale est **la plus mauvaise des deux**. Une maison chauffée au fioul peut ainsi être classée F à cause de ses émissions, même si sa consommation la placerait en D. Le DPE donne aussi une **estimation de facture annuelle** en fourchette, le détail des parois et des équipements, et des recommandations de travaux. Gardez-le : c'est le document qui sert pour vendre, pour louer et pour les aides en rénovation d'ampleur.

### Q: Pourquoi ma facture ne correspond-elle pas à mon DPE ?
`cat: dpe | tags: dpe, facture, ecart, energie_primaire, usage_conventionnel, pre_audit | verif: generique`
R: Parce qu'ils ne mesurent pas la même chose. Le DPE calcule une **consommation conventionnelle** : une maison chauffée à 19 °C partout, tout l'hiver, avec un nombre d'occupants théorique et des usages standards. Votre facture, elle, mesure ce que **vous** consommez réellement. Les écarts viennent souvent :
- de **pièces peu ou pas chauffées**, ou d'une consigne plus basse ;
- d'un **appoint d'une autre énergie** (bois, poêle, bouteille de gaz) qui n'apparaît pas sur la facture d'électricité ;
- de l'**énergie primaire** : pour l'électricité, le DPE compte environ deux kWh « primaires » pour un kWh payé ;
- d'un **DPE réalisé avant un changement d'équipement**, par exemple avant la pose d'une pompe à chaleur ;
- d'une occupation différente : résidence secondaire, absences longues, famille plus nombreuse.
Votre pré-audit compare les deux et vous dit si l'écart est normal. Il calcule toujours les économies sur votre consommation réelle quand vous la renseignez, jamais sur la théorie seule.

### Q: Le calcul du DPE a changé en 2026 : mon étiquette aussi ?
`cat: dpe | tags: dpe, reforme_2026, coefficient_electricite, attestation | verif: reglementation`
R: Peut-être, si votre logement est chauffé à l'électricité. Depuis le 1er janvier 2026, le coefficient qui convertit l'électricité en énergie primaire est passé de 2,3 à 1,9 (arrêté du 13 août 2025). Une maison chauffée à l'électricité ou par une pompe à chaleur peut donc gagner une classe sans aucuns travaux. Votre DPE ne doit pas être refait : depuis le 1er janvier 2026, une attestation mise à jour, qui a la même valeur, peut être obtenue sur l'observatoire DPE de l'ADEME avec le numéro de votre diagnostic. Indiquez dans votre fiche Maison la lettre de cette attestation si elle a changé.

### Q: Pourquoi le pré-audit Hélios ne donne-t-il pas de nouvelle lettre DPE ?
`cat: helios | tags: pre_audit, dpe, limites, audit_reglementaire | verif: generique`
R: Parce que seul un diagnostiqueur certifié peut établir un DPE, et seul un auditeur un audit énergétique réglementaire. Le pré-audit Hélios est une **estimation** : il part de votre fiche Maison (ce que vous avez déclaré, ce que nous supposons quand une information manque) et de votre facture, et il classe les actions selon ce qu'elles vous rapportent. Il ne simule pas le calcul réglementaire du DPE, qui suit une méthode officielle très détaillée. Annoncer une nouvelle lettre serait donc une promesse que nous ne pouvons pas tenir. Si votre projet vise un gain de classes (vente, location, rénovation d'ampleur), c'est l'audit énergétique qui le chiffrera.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/lire_son_dpe.md ».
     Complète les messages de ratio réel / théorique (config.audit_ratio_messages) sans les remplacer. -->

- **explication_ecart_bas** : « Le DPE suppose une maison chauffée à 19 °C partout, tout l'hiver. Votre facture dit ce que vous consommez vraiment : c'est elle qui sert au calcul. »
- **dpe_electrique_2026** : « Votre DPE date d'avant 2026 et votre chauffage est électrique : une attestation mise à jour peut afficher une meilleure lettre. Elle s'obtient sur l'observatoire DPE de l'ADEME. »
