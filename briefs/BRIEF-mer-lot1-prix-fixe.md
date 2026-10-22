# Brief Claude Code — Mises en relation, lot 1 : prix fixe, choix parmi trois, textes publics

## Contexte (à lire avant tout)

Le code des mises en relation (`models/partner.py`, `routers/leads.py`, `routers/partners.py`, `routers/partner_portal.py`, `services/commission.py`) suit l'ancien modèle du doc 08 (juillet 2026) : une **commission de 4 à 10 % du montant des travaux signés**. La stratégie du 19/10/2026 l'a remplacé : **chaque mise en relation est payée à prix fixe par le partenaire**, quel que soit le montant des travaux, pour que les conseils d'Hélios n'aient aucun intérêt à faire dépenser davantage.

Décisions de Stéphane (22/10/2026) :

- **60 € HT par mise en relation, tous métiers**, due **à la transmission**, sauf contestation acceptée (lot 3) ;
- **le foyer choisit** parmi **trois partenaires au plus**, présentés **dans un ordre tiré au sort** ;
- **AD Solar n'est pas partenaire** d'Hélios ;
- Hydrolia et Eolia, sociétés du fondateur, restent partenaires **avec un lien d'intérêt affiché**.

Ce lot change le modèle et les textes. Le dossier transmis et le score (lot 2), l'espace partenaire et les contestations (lot 3), les relevés (lot 4) et le suivi côté foyer (lot 5) viennent ensuite. **Les mises en relation de type `energie` (courtage) ne changent pas.**

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Réglages (`config.py`) | `mer_prix_ht_eur = 60` (commentaire : « validé par Stéphane le 22/10/2026, tous métiers, à ajuster par métier après quelques mois »), `mer_delai_contestation_jours = 7`, `mer_nb_propositions = 3`. |
| Lead | Nouvelle colonne `prix_ht` (figée à la création, copiée du réglage). `commission` et `montant_travaux` restent en base pour l'historique ; **plus aucun calcul de commission** sur les leads `travaux`. `montant_travaux` reste déclaratif, pour les statistiques. |
| Partenaire | Nouvelle colonne `lien_interet` (texte, facultatif), affichée au foyer à côté du nom. Pour Hydrolia et Eolia : « Société créée par le fondateur d'Hélios ». |
| AD Solar | Passe au statut `suspendu` en base (jamais supprimé), retiré de la liste des partenaires réels du script d'amorçage, avec un commentaire « décision de Stéphane du 22/10/2026 : pas partenaire ». |
| Propositions | `GET /leads/propositions?metier=…` : partenaires `actif`, charte signée, couvrant le département de la maison et le métier ; **au plus 3**, tirés au hasard parmi les éligibles, dans un ordre aléatoire. Jamais triés par note ni par ancienneté. Chaque proposition affiche : raison sociale, RGE, note moyenne **seulement à partir de 3 avis**, lien d'intérêt. |
| Garde-fous | Un lead `travaux` exige `statut` = `proprietaire` ou `en_achat` (un locataire reçoit : « Ces travaux se décident avec votre propriétaire »). Pas deux leads actifs vers le même partenaire pour le même métier ; au plus 3 leads actifs par métier et par maison. Le partenaire choisi doit être éligible au moment de la création. |
| Consentement (texte exact) | « J'accepte que ma demande et les informations de mon projet que j'ai choisies soient transmises à {raison sociale}, qui pourra me contacter au sujet de ce projet. » |

**Textes publics à remplacer** (à recopier tels quels, d'abord dans les fiches et `pagesFixes.json` qui les portent, puis dans les composants) :

- **Court** (pied de page, accueil, engagements) : « HELIOS est gratuit pour vous, toujours. Quand vous demandez à être mis en relation avec une entreprise partenaire, celle-ci paie à HELIOS un prix fixe, le même quel que soit le montant de vos travaux, même si vous ne signez rien. Nos conseils n'en dépendent pas. »
- **Partenaires, bloc « Transparence »** : « Chaque entreprise partenaire paie à HELIOS un prix fixe pour chaque mise en relation demandée par un foyer, sans commission sur les travaux. HELIOS n'a donc aucun intérêt à ce que vous dépensiez plus, ni à vous orienter vers une entreprise plutôt qu'une autre. »
- **Devenir partenaire** : « 60 € HT par mise en relation, demandée par un foyer, avec son projet et son consentement. Pas d'abonnement, pas de commission sur vos chantiers. Contestation possible sous 7 jours : coordonnées fausses, hors de votre zone ou de vos métiers, doublon, foyer injoignable après trois essais. »
- **Fiche `kb/faq_maison.md`** (la question sur la rémunération d'Hélios) : réécrire la réponse avec le sens du texte court, sans autre chiffre que le principe du prix fixe.
- **Constitution** (`prompts/`, version en cours) : la phrase sur la « commission auprès des partenaires » devient « la plateforme est payée à prix fixe par les entreprises partenaires pour chaque mise en relation demandée, jamais par le foyer, et sans lien avec le montant des travaux ». La phrase sur SOBRY (courtage) ne change pas.

## Méthode de travail

- Lire `models/partner.py`, `schemas/partner.py`, `routers/leads.py`, `routers/partners.py`, `routers/partner_portal.py`, `services/commission.py`, `scripts/seed_partenaires.py`, `pages/EspaceMisesEnRelation.tsx`, `pages/Partenaires.tsx`, `pages/DevenirPartenaire.tsx`, `pages/Engagements.tsx`, `pages/Home.tsx`, `components/layout/Footer.tsx`, `data/pagesFixes.json`, la constitution en vigueur.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (choix parmi trois, consentement, page partenaires, pied de page). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-mer-lot1.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Données

Migration réversible : `leads.prix_ht`, `partners.lien_interet` ; script de données idempotent pour AD Solar (`suspendu`) et les liens d'intérêt d'Hydrolia et d'Eolia.

## 2. API

- `GET /leads/propositions` (ci-dessus) ; `POST /leads` vérifie l'éligibilité et les garde-fous, fige `prix_ht`.
- `PATCH` de statut (foyer et partenaire) : plus de calcul de commission pour `travaux` ; `services/commission.py` reste pour l'historique et le courtage, avec un commentaire clair.
- Les sorties ne montrent plus de commission au foyer.

## 3. Écran du foyer

« Mises en relation » : choix du métier, les trois propositions (ordre tiré au sort, mention « Ordre tiré au sort » visible), le lien d'intérêt en clair, la case de consentement avec le texte exact, puis la confirmation. Plus aucune ligne « commission HELIOS ».

## 4. Tests

- Propositions : jamais plus de 3, toutes éligibles (zone, métier, actif, charte) ; sur 200 appels, chaque éligible apparaît (tirage réel, pas de tri).
- AD Solar n'est jamais proposé ; Hydrolia et Eolia portent leur lien d'intérêt.
- Garde-fous : locataire refusé, doublon refusé, quatrième lead actif du même métier refusé.
- `prix_ht` = 60 à la création ; aucune commission calculée à `signe` pour un lead `travaux`.
- Les textes publics ne contiennent plus « commission » au sens des travaux (recherche dans `frontend/src` et `kb/`, hors courtage et hors « Commission de régulation de l'énergie »).
- Tests existants verts, build front vert.

## 5. TODO.md

Ajouter un point « Mises en relation, lot 1 » coché après vérification. Ajouter en point ouvert : **faire relire par un avocat le contrat partenaire au nouveau modèle** (doc 08 §5 est écrit pour la commission).

---

## À ne pas faire

- Ne pas toucher aux mises en relation `energie` (courtage) ni aux textes sur SOBRY.
- Ne supprimer aucune colonne ni aucune donnée historique.
- Ne jamais trier les propositions par note, ancienneté ou nombre de leads.
- Pas d'e-mail, pas de paiement.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Un foyer propriétaire choisit parmi au plus trois partenaires tirés au sort, voit les liens d'intérêt, consent avec le texte exact.
2. Chaque mise en relation est figée à 60 € HT ; plus aucune commission sur les travaux.
3. AD Solar n'est jamais proposé.
4. Tous les textes publics décrivent le prix fixe.
5. Tests et build verts, captures jointes, débrief écrit.
