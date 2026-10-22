# Base de connaissances — Locataire : l'entretien, et en parler au propriétaire (source locataire_entretien)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source locataire_entretien).
# Origine : écrit le 22/10/2026 avec le carnet de maison, lot 8 (parcours par statut). La
# « note pour mon propriétaire » du carnet est faite des phrases de la section « Pour la note
# au propriétaire » ci-dessous (après le dernier `---`, non ingérée), recopiées MOT POUR MOT.
# Aucun conseil juridique sur le bail : seulement « sauf clause contraire du bail ».
# À RELIRE PAR STÉPHANE avant de passer en vérifiée (`verif: a_verifier`).

---

### Q: Je suis locataire : quel entretien est à ma charge, et lequel revient au propriétaire ?
`cat: locataire | tags: locataire, entretien, reparations_locatives, chaudiere, ramonage, proprietaire | verif: a_verifier`
R: Le décret n° 87-712 du 26 août 1987 liste les réparations dites locatives : l'entretien courant du logement et de ses équipements, et les menues réparations. C'est à ce titre que l'entretien annuel d'une chaudière individuelle, le ramonage, le nettoyage des bouches de ventilation ou la vérification du détecteur de fumée reviennent en général à l'occupant. Le propriétaire, lui, garde les grosses réparations, le remplacement d'un équipement usé par l'âge ou hors d'usage sans faute de l'occupant, et ce qui touche au bâti. Le carnet d'Helios range chaque tâche d'un côté ou de l'autre selon cette répartition habituelle, sauf clause contraire du bail : c'est votre bail qui fait foi. En cas de doute, l'ADIL de votre département renseigne gratuitement.

### Q: Locataire : comment signaler au propriétaire un entretien en retard ou un équipement ancien ?
`cat: locataire | tags: locataire, proprietaire, courrier, entretien, equipement_ancien | verif: a_verifier`
R: Par écrit, en gardant une trace : un courrier ou un e-mail daté vaut mieux qu'un échange oral. Dites simplement ce que vous constatez — un entretien dont l'échéance est passée, un appareil qui a plus de quinze ans — sans chiffrer ni désigner d'entreprise : c'est au propriétaire de choisir. Le carnet d'Helios peut préparer ce texte à partir de votre calendrier : vous le relisez, le modifiez si besoin et l'envoyez vous-même. Helios n'envoie rien à votre place.

---

## Pour la note au propriétaire

Les phrases de la note, recopiées dans `services/note_proprietaire.py`. La note les assemble
dans cet ordre ; une ligne par tâche, une ligne par équipement, rien d'autre.

- **ouverture** : « Bonjour, je vous écris au sujet de l'entretien du logement que je loue. »
- **taches** : « D'après le calendrier d'entretien que je tiens, ces opérations à votre charge sont dépassées ou arrivent bientôt : »
- **retard** : « échéance dépassée »
- **bientot** : « à prévoir prochainement »
- **equipements** : « Ces équipements ont plus de quinze ans ; je vous les signale pour que vous puissiez anticiper : »
- **rien** : « Je n'ai rien de particulier à signaler pour l'instant : tout est à jour d'après mon calendrier. »
- **bail** : « Je m'appuie sur la répartition habituelle des charges, sauf clause contraire de notre bail. »
- **cloture** : « Je reste disponible pour en parler. Bien cordialement. »
