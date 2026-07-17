# HELIOS — Accès & démarrage rapide

Guide simple pour ouvrir le projet et visiter le site en local.

---

## 🔑 Accès rapide

| | |
|---|---|
| **Site (à ouvrir dans le navigateur)** | http://localhost:5173 |
| **API (technique, pas besoin d'y aller)** | http://localhost:8000 |
| **Documentation API interactive** | http://localhost:8000/docs |
| **Code source (GitHub)** | https://github.com/stf3001/helios |

### Compte de test (espace client)
- **Email :** `test@helios.fr`
- **Mot de passe :** `helios1234`

Ce compte a déjà une fiche maison remplie (~66 %), donc l'espace client, le chat connecté et le simulateur solaire montrent des résultats personnalisés.

> Le simulateur solaire et le chat public sont accessibles **sans compte** :
> http://localhost:5173/simulateur-solaire et http://localhost:5173/helios

---

## ▶️ Démarrer le projet (si les serveurs sont éteints)

Il y a **3 choses à lancer** : la base de données (Docker), l'API, et le site.
Ouvre le terminal dans le dossier `Desktop\HELIOS\helios`.

### 1. La base de données (PostgreSQL + pgvector, via Docker)
Il faut que **Docker Desktop soit lancé** (icône baleine dans la barre des tâches), puis :
```bash
docker compose up -d postgres
```

### 2. L'API (le "cerveau", Python/FastAPI)
```bash
cd api
.venv/Scripts/python -m uvicorn app.main:app --reload
```
Laisse cette fenêtre ouverte.

### 3. Le site (React/Vite) — dans une **autre** fenêtre de terminal
```bash
cd frontend
npm run dev
```
Puis ouvre http://localhost:5173 dans le navigateur.

> ⚠️ Le **chat Helios** répond en 30–60 s : l'IA tourne en local sur le processeur
> (Ollama). C'est normal, ça sera rapide une fois sur le serveur.
> Ollama doit être lancé (il démarre tout seul au démarrage de Windows).

---

## ⏹️ Arrêter le projet
- Fermer les fenêtres de terminal de l'API et du site (ou `Ctrl + C` dedans).
- Arrêter la base : `docker compose down` (les données sont conservées).

---

## 🆘 Si quelque chose ne marche pas
- **Le site ne s'ouvre pas** → vérifier que la fenêtre `npm run dev` tourne.
- **Erreur de connexion / 500** → vérifier que Docker Desktop est lancé et que
  `docker compose up -d postgres` a bien été fait.
- **Le chat ne répond pas** → vérifier qu'Ollama tourne (`ollama list` doit
  afficher `bge-m3` et `llama3.2:3b`).
- **`docker` introuvable dans le terminal** → ajouter au PATH
  `C:\Program Files\Docker\Docker\resources\bin`, ou utiliser le terminal de Docker Desktop.

---
*Détails techniques et avancement des jalons : voir `CLAUDE.md` et le dossier parent (docs 00 à 10).*
