"""Moteur « Mon potentiel hydrique » — production d'eau atmosphérique (Hydrolia).

Porte la logique du calculateur Hydrolia : production (L/jour) par modèle selon la
température et l'humidité, croisée avec le climat mensuel de la ville. Interpolation
bilinéaire sur les tables constructeur.

Les tables constructeur sont PROPRIÉTAIRES : elles vivent dans `api/data/hydrolia/`
(gitignoré, non publié). Si elles sont absentes (ex. clone public), un modèle simplifié
prend le relais pour donner un ordre de grandeur.
"""
import csv
import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parents[2] / "data" / "hydrolia"
MODELS = ["20L", "50L", "100L", "250L", "500L", "1000L"]
LITRES_PAR_PERSONNE_JOUR = 4  # besoin eau de boisson/cuisine indicatif


def _load_table(path: Path) -> dict[int, dict[int, float]]:
    """Charge une table CSV (lignes = humidité, colonnes = température) → {hum: {temp: valeur}}."""
    table: dict[int, dict[int, float]] = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        temps = [int(t) for t in header[1:]]
        for row in reader:
            if not row or not row[0].strip():
                continue
            hum = int(float(row[0]))
            table[hum] = {temps[i]: float(v) for i, v in enumerate(row[1:]) if i < len(temps)}
    return table


@lru_cache(maxsize=1)
def _tables() -> dict[str, dict]:
    """Charge les tables de génération par modèle (vide si les fichiers ne sont pas là)."""
    out: dict[str, dict] = {}
    for m in MODELS:
        p = _DATA / f"{m}_generation.csv"
        if p.exists():
            out[m] = _load_table(p)
    return out


@lru_cache(maxsize=1)
def _meteo() -> dict:
    p = _DATA / "meteo_data.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def available_cities() -> list[str]:
    return list(_meteo().keys())


def _interp(table: dict[int, dict[int, float]], temp: float, hum: float) -> float:
    """Interpolation bilinéaire (température × humidité) dans la table constructeur."""
    hums = sorted(table.keys())
    temps = sorted(next(iter(table.values())).keys())
    hum = max(min(hums), min(max(hums), hum))
    temp = max(min(temps), min(max(temps), temp))
    h0 = max([h for h in hums if h <= hum], default=min(hums))
    h1 = min([h for h in hums if h >= hum], default=max(hums))
    t0 = max([t for t in temps if t <= temp], default=min(temps))
    t1 = min([t for t in temps if t >= temp], default=max(temps))

    def val(h, t):
        return table[h][t]

    if h0 == h1 and t0 == t1:
        return val(h0, t0)
    if h0 == h1:
        return val(h0, t0) + (val(h0, t1) - val(h0, t0)) * (temp - t0) / (t1 - t0)
    if t0 == t1:
        return val(h0, t0) + (val(h1, t0) - val(h0, t0)) * (hum - h0) / (h1 - h0)
    v00, v01, v10, v11 = val(h0, t0), val(h0, t1), val(h1, t0), val(h1, t1)
    ft = (temp - t0) / (t1 - t0)
    a = v00 + (v01 - v00) * ft
    b = v10 + (v11 - v10) * ft
    return a + (b - a) * (hum - h0) / (h1 - h0)


def _fallback_daily(model: str, temp: float, hum: float) -> float:
    """Estimation grossière si les tables constructeur sont absentes (ordre de grandeur)."""
    nominal = float(model.replace("L", ""))
    facteur = max(0.0, (0.35 + 0.65 * hum / 100) * (0.25 + 0.75 * max(temp, 0) / 35))
    return round(nominal * min(facteur, 1.0), 1)


def water_potential(city: str, model: str) -> dict:
    """Production d'eau estimée pour une ville et un modèle : par mois, annuel, moyenne/jour."""
    meteo = _meteo().get(city)
    if meteo is None:
        raise ValueError(f"Ville inconnue : {city}")
    tables = _tables()
    table = tables.get(model)
    exact = table is not None

    monthly = []
    total_annual = 0.0
    for month in range(1, 13):
        md = meteo["monthly_data"][str(month)]
        t, h = md["temperature"], md["humidity"]
        daily = _interp(table, t, h) if exact else _fallback_daily(model, t, h)
        days = 30
        litres_mois = round(daily * days)
        monthly.append({"mois": month, "litres_jour": round(daily, 1), "litres_mois": litres_mois})
        total_annual += litres_mois

    moyenne_jour = round(total_annual / 365, 1)
    personnes = round(moyenne_jour / LITRES_PAR_PERSONNE_JOUR, 1)
    return {
        "ville": city,
        "modele": model,
        "source": "tables_constructeur" if exact else "estimation_simplifiee",
        "production_annuelle_litres": round(total_annual),
        "moyenne_litres_jour": moyenne_jour,
        "personnes_couvertes": personnes,
        "mensuel": monthly,
        "avertissement": "Estimation indicative selon le climat moyen de la ville ; la production réelle "
                         "dépend des conditions locales. Ne remplace pas un dimensionnement par un professionnel.",
    }
