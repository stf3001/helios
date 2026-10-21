# Brief Claude Code — Remplacer les quatre experts inventés (point 4)

## Contexte (à lire avant tout)

Point 4 de `TODO.md` : `frontend/src/pages/HeliosIA.tsx` (constante `EQUIPE`) présente quatre conseillers qui n'existent pas (Camille, Yanis, Hélène, Karim), avec âge, région, parcours et années d'expérience. Juste en dessous, le visiteur réserve un appel « avec quelqu'un de notre équipe ». C'est contraire à la charte (transparence, honnêteté).

Décision de Stéphane (21/10/2026) : **Stéphane, plus trois profils, Léna, Cora et Lenny**, pour couvrir énergie, construction, juridique et jardin. Pour rester honnête, la page les présente comme ce qu'ils sont :

- **Stéphane** : une personne réelle, fondateur d'Hélios. C'est lui qui prend les rendez-vous téléphoniques.
- **Léna, Cora, Lenny** : les **voix spécialisées de l'assistant Hélios**, des personnages d'IA, annoncés comme tels. Aucun âge, aucune région, aucune année d'expérience, aucun parcours professionnel inventé.

Fichiers concernés : `frontend/src/pages/HeliosIA.tsx`, éventuellement `frontend/src/components/AvatarExpert.tsx`, `TODO.md`.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Profil | Rôle affiché | Texte (à recopier tel quel) |
|---|---|---|
| Stéphane | Fondateur d'Hélios | « Stéphane a fondé Hélios. Il a passé vingt-quatre ans dans la restauration avant de consacrer cinq ans au conseil en énergie solaire chez les particuliers. C'est lui qui vous rappelle quand vous réservez un appel. » |
| Léna | Voix énergie de l'assistant | « Léna est la voix d'Hélios pour l'énergie : factures, contrats, solaire, chauffage. C'est une intelligence artificielle : elle s'appuie sur les moteurs de calcul d'Hélios et le dit quand elle n'est pas sûre. » |
| Cora | Voix construction et rénovation | « Cora est la voix d'Hélios pour la maison et les travaux : isolation, ventilation, entretien, garanties. C'est une intelligence artificielle : elle ne remplace ni un diagnostic, ni un professionnel sur place. » |
| Lenny | Voix juridique et jardin | « Lenny est la voix d'Hélios pour les règles et le terrain : urbanisme, obligations d'entretien, débroussaillement, potager. C'est une intelligence artificielle : il cite ses sources et ne donne pas d'avis juridique. » |

- Le texte de Stéphane est une proposition : **le signaler dans le résumé pour validation** avant de cocher le point 4. Aucune mention d'employeur.
- Une **étiquette visible** sur chaque carte : « Personne réelle » pour Stéphane, « Assistant IA » pour les trois autres.
- Les avatars dessinés restent pour Léna, Cora et Lenny. Pour Stéphane : **pas de photo inventée ni de dessin de visage** ; un monogramme « S » dans la charte, en attendant une vraie photo.
- Le texte au-dessus du bloc de réservation devient : « Gratuit, sans engagement, avec Stéphane, au téléphone. Choisissez le moment qui vous arrange : il vous rappelle. »

## Méthode de travail

- Lire `HeliosIA.tsx` et `AvatarExpert.tsx`. Plan court, un commit, message en français.
- À la fin : capture de la section (bureau et 375 px). **Attendre la validation de Stéphane.**
- Cocher le point 4 de `TODO.md` après vérification, en citant le commit.

## À ne pas faire

- Aucun âge, aucune région, aucune ancienneté, aucun diplôme ni employeur pour Léna, Cora et Lenny.
- Ne pas faire croire qu'un des trois peut être joint au téléphone.
- Ne pas brancher ces voix dans le chat dans ce lot (un aiguillage par thème pourra venir plus tard).
- Ne pas modifier le reste de la page.
- **Aucune nouvelle dépendance.**

## Critères d'acceptation

1. Plus aucune personne inventée sur le site (vérifier par une recherche des quatre anciens prénoms dans `frontend/src`).
2. Chaque carte dit clairement s'il s'agit d'une personne réelle ou d'un assistant IA.
3. La réservation annonce un appel avec Stéphane.
4. Build front vert, captures jointes, point 4 coché.
