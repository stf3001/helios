# KB — base de connaissances versionnée
Sources : FAQ (docs de cadrage 05) + chunks curés (KB/).
`python agents/ingest.py` (jalon 3) : parse ces fichiers -> embeddings -> pgvector.
Format d'une entrée : voir 05-FAQ-V1.md (1 entrée = 1 chunk, métadonnées cat/tags/verif).
