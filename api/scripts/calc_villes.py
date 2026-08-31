"""Précalcule les données solaires RÉELLES par ville, à committer une fois.

Pourquoi précalculer et versionner plutôt que d'appeler PVGIS au build : le build reste
hors ligne et reproductible, et on n'inflige pas une rafale d'appels au service européen
à chaque déploiement. Les données changent très peu d'une année sur l'autre.

Chaque ville obtient une production réellement différente : c'est ce qui distingue une page
locale légitime d'une page géographique dupliquée, que les moteurs sanctionnent.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\DELL\Desktop\HELIOS\helios\api")))

from app.services import pvgis  # noqa: E402
from app.services.solar_engine import cout_installation_eur  # noqa: E402

SORTIE = Path(r"C:\Users\DELL\Desktop\HELIOS\helios\frontend\src\data\villes.json")

# Zone climatique réglementaire (RT/RE) — détermine les besoins de chauffage :
# H1 = plus froid (nord/est/montagne), H2 = tempéré (ouest/centre), H3 = méditerranéen.
VILLES = [
    ("Paris",        48.8566,  2.3522, "75", "H1"),
    ("Lyon",         45.7640,  4.8357, "69", "H1"),
    ("Marseille",    43.2965,  5.3698, "13", "H3"),
    ("Toulouse",     43.6047,  1.4442, "31", "H2"),
    ("Bordeaux",     44.8378, -0.5792, "33", "H2"),
    ("Nantes",       47.2184, -1.5536, "44", "H2"),
    ("Montpellier",  43.6108,  3.8767, "34", "H3"),
    ("Strasbourg",   48.5734,  7.7521, "67", "H1"),
    ("Lille",        50.6292,  3.0573, "59", "H1"),
    ("Rennes",       48.1173, -1.6778, "35", "H2"),
    ("Nice",         43.7102,  7.2620, "06", "H3"),
    ("Grenoble",     45.1885,  5.7245, "38", "H1"),
]


async def main() -> None:
    out = []
    for nom, lat, lon, dep, zone in VILLES:
        # Hypothèse affichée sur la page : toiture plein sud, 30°, sans ombrage.
        prods = {}
        for kwc in (3, 6, 9):
            r = await pvgis.production_for_power(
                lat=lat, lon=lon, peakpower=kwc, angle=30, aspect=0, loss=14.0)
            prods[kwc] = round(r["annual_kwh"])
        p6 = prods[6]
        out.append({
            "nom": nom, "slug": nom.lower().replace(" ", "-"),
            "departement": dep, "zone": zone,
            "prod_3kwc": prods[3], "prod_6kwc": p6, "prod_9kwc": prods[9],
            "cout_6kwc": round(cout_installation_eur(6)),
        })
        print(f"  {nom:14} {p6:>6} kWh/an pour 6 kWc  (zone {zone})", flush=True)

    SORTIE.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ecart = max(v["prod_6kwc"] for v in out) / min(v["prod_6kwc"] for v in out)
    print(f"\n{len(out)} villes -> {SORTIE.name}")
    print(f"écart production min/max : x{ecart:.2f}  (si proche de 1, les pages seraient trop semblables)")


asyncio.run(main())
