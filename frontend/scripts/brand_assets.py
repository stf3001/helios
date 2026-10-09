r"""Produit les images de marque a partir de la charte « carnet de maison ».

    api\.venv\Scripts\python.exe frontend/scripts/brand_assets.py

Pourquoi un script et non des fichiers deposes a la main : la refonte du 30/09/2026 a
change le site entier mais PAS les PNG, qui sont restes a l'ancienne charte orange
pendant six jours sans que rien ne le signale (point 16 de TODO.md). Un dessin qui se
regenere suit la charte ; un fichier binaire, non.

Le dessin est le meme soleil au trait que `src/components/MarqueHelios.tsx` et
`public/favicon.svg` : huit rayons et un disque, dans un repere de 32 unites. Il est
RECOPIE ici plutot qu'importe — un script Python ne lit pas un composant React — donc
**si le dessin change la-bas, il change ici**. C'est la seule duplication du fichier.

Le trace passe par un sur-echantillonnage x4 puis une reduction : Pillow ne lisse pas
les bords, et un rayon de 1 px non lisse se voit a toutes les tailles.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parents[1]
PUBLIC = RACINE / "public"
POLICES = PUBLIC / "fonts"

# Les jetons de `src/index.css`, en RVB. Ils se tiennent a jour ENSEMBLE (cf. CLAUDE.md).
TERRACOTTA = (168, 66, 15)      # --h-accent
SABLE = (245, 239, 228)         # --h-sable
BORD = (226, 216, 198)          # --h-bord
INK = (27, 42, 47)              # --h-ink
TEXTE_2 = (74, 90, 95)          # --h-texte-2

SUR = 4  # facteur de sur-echantillonnage

# Geometrie du soleil, dans le repere de 32 unites du SVG.
CENTRE = 16.0
RAYON_DISQUE = 6.6
RAYON_INTERIEUR = 9.2    # debut d'un rayon (y = 6.8 dans le SVG)
RAYON_EXTERIEUR = 12.8   # fin d'un rayon (y = 3.2)
ENVERGURE = 2 * RAYON_EXTERIEUR / 32  # le soleil occupe 80 % du repere


def _dessiner_soleil(d: ImageDraw.ImageDraw, cx: float, cy: float, cote: float,
                     couleur: tuple[int, int, int], epaisseur_svg: float = 1.5) -> None:
    """Pose le soleil centre sur (cx, cy), le repere de 32 unites tenant dans `cote`."""
    echelle = cote / 32
    trait = max(epaisseur_svg * echelle, 1.0)
    rayon_cap = trait / 2

    for i in range(8):
        angle = math.radians(i * 45 - 90)  # -90 : le premier rayon pointe vers le haut
        dx, dy = math.cos(angle), math.sin(angle)
        x1, y1 = cx + dx * RAYON_INTERIEUR * echelle, cy + dy * RAYON_INTERIEUR * echelle
        x2, y2 = cx + dx * RAYON_EXTERIEUR * echelle, cy + dy * RAYON_EXTERIEUR * echelle
        d.line((x1, y1, x2, y2), fill=couleur, width=round(trait))
        # Les bouts ronds du SVG (`stroke-linecap="round"`) : Pillow ne les fait pas.
        for x, y in ((x1, y1), (x2, y2)):
            d.ellipse((x - rayon_cap, y - rayon_cap, x + rayon_cap, y + rayon_cap), fill=couleur)

    r = RAYON_DISQUE * echelle
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=couleur, width=round(trait))


def _toile(largeur: int, hauteur: int, fond: tuple[int, int, int] | None) -> Image.Image:
    """Une toile sur-echantillonnee, transparente ou remplie."""
    couleur = (*fond, 255) if fond else (0, 0, 0, 0)
    return Image.new("RGBA", (largeur * SUR, hauteur * SUR), couleur)


def _reduire(im: Image.Image, largeur: int, hauteur: int) -> Image.Image:
    return im.resize((largeur, hauteur), Image.LANCZOS)


def icone(cote: int, fond: tuple[int, int, int] | None, occupation: float,
          epaisseur_svg: float = 1.5) -> Image.Image:
    """Une icone carree. `occupation` = part du cote occupee par le soleil (sans le fond)."""
    im = _toile(cote, cote, fond)
    d = ImageDraw.Draw(im)
    milieu = cote * SUR / 2
    _dessiner_soleil(d, milieu, milieu, cote * SUR * occupation / ENVERGURE, TERRACOTTA, epaisseur_svg)
    return _reduire(im, cote, cote)


def _police(fichier: str, taille: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(POLICES / fichier), taille)


def _centrer(d: ImageDraw.ImageDraw, texte: str, police: ImageFont.FreeTypeFont,
             milieu_x: float, y: float, couleur: tuple[int, int, int]) -> None:
    d.text((milieu_x, y), texte, font=police, fill=couleur, anchor="mt")


def image_de_partage() -> Image.Image:
    """L'apercu 1200x630 des reseaux et des messageries — l'image la plus vue du site."""
    L, H = 1200, 630
    im = _toile(L, H, SABLE)
    d = ImageDraw.Draw(im)

    # Le filet de la charte : les surfaces du site se detachent par une bordure 1px,
    # jamais par une ombre. A l'echelle de l'image, 2 px.
    marge = 28 * SUR
    d.rectangle((marge, marge, L * SUR - marge, H * SUR - marge), outline=(*BORD, 255), width=2 * SUR)

    milieu = L * SUR / 2
    _dessiner_soleil(d, milieu, 160 * SUR, 150 * SUR / ENVERGURE, TERRACOTTA, epaisseur_svg=1.5)

    _centrer(d, "Helios", _police("instrument-serif-latin.woff2", 128 * SUR), milieu, 250 * SUR, INK)
    _centrer(d, "La maison a enfin son expert",
             _police("instrument-serif-italic-latin.woff2", 54 * SUR), milieu, 404 * SUR, TERRACOTTA)
    _centrer(d, "Diagnostic énergétique indépendant · gratuit · à votre rythme",
             _police("jakarta-latin.woff2", 27 * SUR), milieu, 500 * SUR, TEXTE_2)

    return _reduire(im, L, H)


def main() -> None:
    sorties: list[tuple[Path, Image.Image]] = [
        # Le repli du favicon SVG, pour les navigateurs anciens : meme fond transparent et
        # meme trait epaissi que `public/favicon.svg`, ou a 16 px un trait de 1,5 disparait.
        (PUBLIC / "favicon-32.png", icone(32, None, ENVERGURE, epaisseur_svg=2.0)),
        # iOS ne pose aucun fond derriere l'icone : il lui en faut un.
        (PUBLIC / "apple-touch-icon.png", icone(180, SABLE, 0.62)),
        (PUBLIC / "icon-192.png", icone(192, SABLE, 0.62)),
        (PUBLIC / "icon-512.png", icone(512, SABLE, 0.62)),
        # « maskable » : Android recadre jusqu'a un cercle de 80 % du cote. Le dessin tient
        # donc dans 45 %, et le fond va d'un bord a l'autre.
        (PUBLIC / "icon-maskable-512.png", icone(512, SABLE, 0.45)),
        # Le bandeau du PDF de pre-audit (`api/app/services/pdf_audit.py`), pose sur un
        # fond creme : transparent, carre, et c'est le seul usage de ce fichier.
        (PUBLIC / "brand" / "logo-mark.png", icone(512, None, 0.92)),
        (PUBLIC / "og-image.png", image_de_partage()),
    ]

    for chemin, image in sorties:
        if chemin.name == "og-image.png":
            image = image.convert("RGB")  # pas de transparence : certains clients la noircissent
        image.save(chemin, optimize=True)
        print(f"  {chemin.relative_to(RACINE)}  {image.size[0]}x{image.size[1]}  "
              f"{chemin.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()
