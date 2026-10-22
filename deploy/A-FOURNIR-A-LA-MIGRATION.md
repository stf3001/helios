# À fournir à la migration (mise en ligne)

Établi le 21/10/2026, quand HELIOS tournait encore en local. Ce qui suit est **prêt dans le
code** et n'attend qu'une valeur. Chaque ligne dit quoi, où le mettre, et ce qui se passe tant
que c'est vide. Les valeurs vont dans le `.env` du serveur, jamais dans git.

## Les valeurs à renseigner

| Variable (`.env`) | Ce que c'est | Tant que c'est vide |
|---|---|---|
| `FRONTEND_URL` | L'adresse du site (`https://…`) | `http://localhost:5173`. Elle sert aussi au **CORS** (`main.py`) et aux liens des e-mails : à changer, sinon le site en ligne ne peut pas appeler l'API. |
| `HELIOS_SITE_URL` | Le domaine, pour le pré-rendu SEO (canoniques, plan de site) | À définir **avant** `npm run build` : une canonique vers le mauvais domaine fait perdre l'indexation. |
| `COOKIE_SECURE=true` | Cookie de session en HTTPS seulement | `False` en local. À passer à `true` dès que le site est en HTTPS. |
| `JWT_SECRET`, `ADMIN_TOKEN` | Deux secrets longs et aléatoires | Valeurs `change-me` du `.env.example` : **à remplacer impérativement**. |
| `POSTGRES_*`, `DATABASE_URL` | La base du serveur | Base locale Docker. Puis `alembic upgrade head` (migrations jusqu'à 0028). |
| `EMAIL_API_KEY` | Clé du fournisseur d'e-mail (Resend ou Brevo, **à choisir**) | Aucun e-mail ne part : vérification de compte, lead partenaire, rendez-vous et rappels d'entretien sont journalisés (point 1 de `TODO.md`). Il faudra aussi écrire l'appel au fournisseur choisi (les `TODO(J9)` de `api/app/services/email.py`) et une adresse d'expédition sur le domaine. |
| `RDV_NOTIFICATION_EMAIL` | Qui reçoit un rendez-vous réservé | Une ligne de journal, sans nom ni téléphone. Le message est déjà écrit (`email.send_rdv_notification`). |
| `LLM_API_KEY` | Clé Anthropic (Claude) | Tout reste sur le modèle local. **Le compte Anthropic doit avoir du crédit** : au 21/10/2026 il était épuisé (point 42). |
| `LLM_API_BUDGET_DAILY_EUR`, `…_MONTHLY_EUR`, `LLM_API_DAILY_REQUESTS_PER_USER` | Plafonds de coût et quota par client | Valeurs de développement (1 € / 10 € / 3 par jour) : à remonter pour la production. |
| `OLLAMA_URL` | Le modèle local et les embeddings | `http://localhost:11434` : Ollama doit tourner sur le serveur (ou ailleurs, adresse à donner). |
| `METEOFRANCE_API_KEY` | Clé de l'API « Bulletin Vigilance » de Météo-France (compte gratuit sur portail-api.meteofrance.fr, souscrire à `DonneesPubliquesVigilance`). Envoyée dans l'en-tête `apikey` ; si le portail ne donne qu'un jeton OAuth2, adapter `meteofrance_vigilance._entetes`. | Module dormant : aucun appel, aucun bandeau. Puis lancer la collecte toutes les heures (`python -m scripts.collecter_vigilance`), par le planificateur du serveur. |

## Les décisions à prendre (pas techniques)

- **Rendez-vous** : qui reçoit, qui décroche, et sur quelles heures. Les plages de `config.py`
  (`rdv_plages_horaires` : 9 h-12 h 30 et 14 h-18 h, lundi-vendredi) sont inventées (point 45).
- **Le fournisseur d'e-mail** : Resend ou Brevo.

## Les vérifications le jour J

- `deploy/nginx.conf` : la directive `try_files $uri $uri.html $uri/ /index.html` est
  indispensable au pré-rendu des fiches (sans elle, les moteurs voient une page vide).
- Le fuseau : le code calcule l'heure de Paris lui-même (été comme hiver, `creneaux.py`) ;
  l'horloge du serveur peut rester en UTC.
- Un premier rendez-vous de test, pour voir arriver l'e-mail et la ligne dans le back-office.
- La journalisation : uvicorn n'affiche pas le niveau INFO des journaux `helios.*` (liens de
  vérification et notifications « non envoyées » en mode dev). Configurer le niveau de
  journalisation du serveur pour les voir. Le repli API → local, lui, journalise en WARNING.
