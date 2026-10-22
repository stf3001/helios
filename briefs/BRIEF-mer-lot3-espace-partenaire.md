# Brief Claude Code — Mises en relation, lot 3 : l'espace partenaire, la charte et les contestations

## Contexte (à lire avant tout)

Prérequis : **lots 1 et 2 validés**.

L'espace partenaire existe (`routers/partner_portal.py`, `pages/PartnerPortal.tsx`) : connexion, liste des leads, changement de statut. Il lui manque ce qui rend le modèle tenable : le **dossier lisible**, la **contestation** sous 7 jours, les **justificatifs** (Kbis, décennale, RGE) avec leurs dates, la **charte signée** et une file de traitement côté administration. Tout reste en local, **sans e-mail** : l'activation d'un compte partenaire se fait par un lien que l'administration copie et transmet elle-même.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Motifs de contestation | `coordonnees_fausses`, `hors_zone_ou_metier`, `doublon` (même foyer, même métier, déjà transmis à ce partenaire dans les 12 mois, par Hélios ou en direct), `injoignable` (trois essais à des créneaux donnés par le foyer, dates à saisir). Commentaire obligatoire. |
| Délai | 7 jours calendaires après la transmission (`mer_delai_contestation_jours`). Au-delà, le bouton disparaît. |
| Traitement | L'administration accepte ou refuse, avec un motif. Acceptée → le lead n'est plus facturable (`prix_ht` gardé, `facturable = false`). |
| Justificatifs | Kbis (de moins de 3 mois à la candidature), attestation d'assurance décennale (date de fin), qualification RGE si déclarée (date de fin). Un justificatif expiré : le partenaire **sort des propositions** (lot 1) jusqu'au nouveau dépôt, garde l'accès à ses leads, et voit une alerte. |
| Charte | Le texte de la charte partenaire (doc 01, mis au nouveau modèle de prix) est stocké avec une **version**. Le partenaire la signe dans son espace (horodatage, version). Une nouvelle version demande une nouvelle signature ; sans elle, il sort des propositions. |
| Activation | À la validation d'une candidature, l'administration obtient un **lien d'activation à usage unique** (valable 7 jours) à copier ; le partenaire y choisit son mot de passe. |
| Suivi déclaratif | Le partenaire déclare `contacte` (date), `devis` (montant facultatif), `signe` (montant facultatif), `perdu` (motif). C'est pour les statistiques et le foyer, **sans effet sur le prix**. |

## Méthode de travail

- Lire les débriefs des mer lots 1 et 2, `routers/partner_portal.py`, `pages/PartnerPortal.tsx`, `routers/admin.py` (partenaires), `pages/DevenirPartenaire.tsx`, `routers/documents.py` (motif d'envoi de fichiers), le doc 01 du dossier parent pour la charte.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (liste des leads, dossier, contestation, justificatifs, charte ; côté admin : candidature, contestations). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-mer-lot3.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Données

Migration réversible : table `contestations` (lead, motif, commentaire, dates d'essais, statut `en_attente|acceptee|refusee`, motif de décision, dates) ; colonne `leads.facturable` (défaut vrai) ; table `partner_documents` (partenaire, type, fichier, date de fin, statut) ; table `chartes` (version, texte, date) et `partners.charte_version_signee` ; jetons d'activation (haché, expiration, usage unique).

## 2. Charte

Écrire la charte partenaire v2 dans `kb/charte_partenaire.md` (fichier de texte de référence, **non ingéré dans le chat**), à partir du doc 01 et du nouveau modèle : remplacer la « loyauté » sur les commissions par l'engagement de **contacter le foyer seulement dans ses créneaux et pour ce projet**, de **ne pas revendre ni céder** le lead, et de **respecter l'interdiction du démarchage**. Marquer `a_relire: Stéphane`. Elle sera relue avant le premier partenaire réel.

## 3. Espace partenaire

- Leads : du plus récent au plus ancien, score et créneaux visibles, dossier complet (lot 2), statut déclaratif, bouton « Contester » tant que le délai court.
- Mon entreprise : zones, métiers, justificatifs (dépôt, date de fin, état), charte (version signée ou à signer).
- Une bannière claire en cas de justificatif expiré ou de charte à signer.

## 4. Administration

- Candidatures : justificatifs, validation, création du lien d'activation (copiable), refus motivé.
- Contestations : file `en_attente`, décision en un clic avec motif.
- Partenaires : justificatifs à échéance dans les 30 jours.
- Chaque action tracée dans le journal des accès admin.

## 5. Tests

- Contestation : refusée après 7 jours ; acceptée → `facturable = false` ; refusée → inchangé.
- Justificatif expiré ou charte non signée → partenaire absent des propositions, leads toujours visibles.
- Lien d'activation : usage unique, expiré après 7 jours.
- Un partenaire ne voit que ses leads.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Pas d'e-mail ni de notification : l'administration transmet les liens elle-même.
- Le statut déclaratif ne modifie jamais le prix ni la facturabilité (seule une contestation acceptée le fait).
- Ne pas publier la charte v2 sur le site avant la relecture de Stéphane.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Un partenaire lit ses dossiers, déclare son suivi, conteste dans le délai.
2. L'administration valide les candidatures, active les comptes sans e-mail, tranche les contestations.
3. Un partenaire sans justificatif valide ou sans charte signée n'est plus proposé aux foyers.
4. Tests et build verts, captures jointes, débrief écrit.
