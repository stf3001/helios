# Base de connaissances — Remplacer ses fenêtres (source action_menuiseries)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source action_menuiseries).
# Fiche « action » du pré-audit. Complète faq_maison.md (« Changer les fenêtres, est-ce prioritaire ? »,
# « Double ou triple vitrage ? ») sans les répéter. Aucune marque, aucun installateur.

---

### Q: Remplacer mes fenêtres est-il rentable dans mon cas ?
`cat: menuiseries | tags: fenetres, rentabilite, pre_audit, simple_vitrage | verif: generique`
R: Sur la seule facture, presque jamais rapidement. Les fenêtres pèsent souvent autour d'un dixième des pertes d'une maison, et chaque fenêtre posée coûte cher. Passer du double vitrage ancien au double vitrage récent ne rapporte que quelques euros par fenêtre et par an. Le remplacement se justifie pour d'autres raisons, qui sont souvent les vraies :
- du **simple vitrage**, des courants d'air, de la condensation qui coule sur les appuis ;
- des **menuiseries abîmées** : bois pourri, fermetures qui forcent, joints morts ;
- le **bruit** (route, voisinage, aéroport) ;
- la **sécurité** et le confort d'usage.
Votre pré-audit chiffre l'économie d'énergie et classe souvent les fenêtres « au remplacement en fin de vie ». Si l'une de ces raisons vous concerne, elle peut suffire à décider, en connaissance de cause.

### Q: Avant de changer mes fenêtres, que puis-je faire pour presque rien ?
`cat: menuiseries | tags: fenetres, joints, sobriete, petits_travaux | verif: generique`
R: Beaucoup, et c'est souvent bluffant.
- **Des joints neufs** sur les ouvrants : quelques euros par fenêtre, et les courants d'air disparaissent.
- **Le réglage des ouvrants** : une fenêtre qui ne plaque plus contre son cadre laisse passer l'air. Un serrurier ou un menuisier règle les ferrures en quelques minutes.
- **Le calfeutrement des coffres de volets roulants**, souvent de vraies passoires : un kit d'isolation de coffre suffit.
- **Les rideaux épais et les volets fermés la nuit** en hiver, et fermés le jour côté soleil en été.
Gardez les **entrées d'air** dégagées : ce ne sont pas des fuites, c'est votre ventilation.

### Q: Au-delà des économies, qu'apportent des fenêtres neuves ?
`cat: menuiseries | tags: fenetres, confort, acoustique, condensation, securite | verif: generique`
R: Du confort près des vitrages, où l'on ne sent plus le froid. Beaucoup moins de bruit, surtout avec un vitrage acoustique (vitres d'épaisseurs différentes). La fin de la condensation sur le vitrage, si la ventilation suit. Une meilleure sécurité. Et dans le Sud, l'occasion de penser à l'été : des protections solaires extérieures (volets, brise-soleil, stores) protègent bien mieux de la chaleur qu'un vitrage, même performant.

### Q: Quels pièges éviter lors du remplacement des fenêtres ?
`cat: menuiseries | tags: fenetres, vigilance, ventilation, urbanisme, pose | verif: reglementation`
R: Les plus fréquents :
- **La ventilation.** Des fenêtres étanches suppriment les fuites d'air qui ventilaient la maison malgré vous. Sans VMC ni entrées d'air, l'humidité monte : buée, moisissures, air vicié. Vérifiez la ventilation avant ou en même temps que le chantier.
- **La pose « en rénovation »** sur l'ancien cadre : elle est rapide et propre, mais elle réduit la surface vitrée, donc la lumière. La dépose totale coûte plus cher mais garde le clair de jour. Faites-vous montrer la différence.
- **L'urbanisme** : changer l'aspect (matériau, couleur, petits bois) demande souvent une déclaration préalable, et l'accord de l'architecte des Bâtiments de France en secteur protégé.
- **Le calfeutrement** entre la fenêtre et le mur : c'est là que se joue l'étanchéité. Une belle fenêtre mal posée reste une passoire.
- **Les coffres de volets roulants**, à isoler en même temps.

### Q: Que doit contenir un devis de fenêtres ?
`cat: menuiseries | tags: fenetres, devis, Uw, Sw, rge | verif: reglementation`
R: Pour chaque fenêtre : les dimensions, le matériau (PVC, bois, aluminium, mixte), le type de pose (dépose totale ou en rénovation) et les performances. Le coefficient **Uw** mesure l'isolation : plus il est bas, mieux c'est (repère : Uw ≤ 1,3). Le facteur solaire **Sw** indique la chaleur du soleil qui entre : utile en hiver au sud, gênant en été à l'ouest. Le devis précise aussi les entrées d'air, le calfeutrement et l'habillage intérieur et extérieur, l'évacuation des anciennes fenêtres, la qualification RGE, la TVA à 5,5 % et la prime CEE éventuelle.

### Q: Quelles aides pour remplacer mes fenêtres en 2026 ?
`cat: aides | tags: fenetres, maprimerenov, cee, renovation_ampleur | verif: date_sensible_20_10_2026`
R: Pour tout dossier déposé **depuis le 1er septembre 2026**, le remplacement des fenêtres **n'est plus financé par MaPrimeRénov' par geste** (décret n° 2026-822 du 25 août 2026). Il reste finançable en **rénovation d'ampleur** (logement E, F ou G, gain d'au moins deux classes, accompagnateur obligatoire). Les **primes CEE** restent possibles pour le remplacement d'un simple vitrage, avec un montant variable selon l'organisme. La **TVA à 5,5 %** s'applique quand les performances minimales sont atteintes.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/action_menuiseries.md ». -->

- **pourquoi_rentable** : « Du simple vitrage avec {chauffage} : vos fenêtres vous coûtent cher, et le confort y gagnera autant que la facture. »
- **pourquoi_peu_rentable** : « Vos fenêtres pèsent peu dans vos pertes : les changer ne se rembourse pas sur l'énergie. Faites-le en fin de vie, ou pour le bruit et le confort. En attendant, des joints neufs font déjà beaucoup. »
- **benefices** : moins de bruit · plus de sensation de froid près des vitres · fin de la condensation (avec une ventilation adaptée)
- **vigilance** : ventilation à vérifier · pose en rénovation = moins de lumière · déclaration préalable si l'aspect change
- **devis** : Uw ≤ 1,3 · type de pose · entrées d'air et calfeutrement
