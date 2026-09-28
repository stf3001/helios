"""Les messages qui ne sont pas des questions — salutations, remerciements, « allo ? ».

POURQUOI CE MODULE. Un « allo ?? » partait dans toute la chaîne : calcul d'embedding,
recherche vectorielle, puis rédaction par le modèle local, qui prend 30 à 60 secondes sur
un processeur. Il en revenait un pavé de six lignes qui TUTOYAIT le visiteur, alors que la
constitution dit « vouvoiement par défaut » et « réponses courtes par défaut ». Un petit
modèle local n'applique pas une consigne enterrée dans un long prompt : insister dans le
prompt n'y aurait rien changé. On ne l'appelle donc pas.

Ici la réponse est ÉCRITE, pas générée. Elle sort en quelques millisecondes, elle vouvoie,
elle tient en une ligne, et elle ramène vers une vraie question — ce qu'un « Qu'est-ce qui
vous amène aujourd'hui ? » de six lignes ne faisait pas mieux.

CE QUI N'EST PAS ICI. Toute question de fond, même mal formulée, même très courte
(« solaire ? »), doit passer par la base de connaissances. Le filet est donc volontairement
étroit : on compare le message ENTIER à une liste fermée. « bonjour » répond ici ;
« bonjour, ai-je intérêt au solaire ? » n'y touche pas et suit son chemin normal.
"""

import re
import unicodedata

#: Chaque entrée : (formulations exactes, réponse). La réponse est courte, elle vouvoie,
#: et elle propose la suite — un visiteur qui dit « bonjour » attend qu'on l'accueille,
#: pas qu'on l'interroge.
#:
#: Les formulations sont écrites SOUS FORME NORMALISÉE (minuscules, sans accent, sans
#: apostrophe) : c'est ce que produit `normaliser()`, et les comparer autrement ne
#: marcherait pas.
_CIVILITES: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("bonjour", "bonsoir", "salut", "hello", "coucou", "bjr", "slt", "hey",
         "bonjour a tous", "bonjour helios", "salut helios", "bonjour a vous"),
        "Bonjour ! Dites-moi ce qui vous amène : une facture qui grimpe, des travaux en "
        "tête, un devis à relire ?",
    ),
    (
        ("allo", "alo", "allo allo", "il y a quelqu un", "y a quelqu un", "tu es la",
         "t es la", "vous etes la", "ca marche", "ca fonctionne", "test", "tests",
         "?", "??", "???"),
        "Je suis là 🙂 Posez votre question sur votre logement, je vous réponds tout de suite.",
    ),
    (
        ("merci", "merci beaucoup", "merci bien", "mille mercis", "nickel", "super",
         "parfait", "genial", "ok", "oki", "d accord", "tres bien", "top"),
        "Avec plaisir. Si autre chose vous chiffonne sur votre logement, je suis là.",
    ),
    (
        ("au revoir", "bye", "ciao", "a bientot", "bonne journee", "bonne soiree",
         "a plus", "bonne nuit", "adieu"),
        "Bonne journée ! Revenez quand vous voulez, vos études vous attendent.",
    ),
    (
        ("ca va", "comment ca va", "comment vas tu", "comment allez vous", "tu vas bien",
         "vous allez bien"),
        "Très bien, merci 🙂 Et chez vous, côté énergie, qu'est-ce qui vous préoccupe ?",
    ),
    (
        ("qui es tu", "tu es qui", "qui etes vous", "vous etes qui", "c est quoi helios",
         "qu est ce que helios", "tu sers a quoi", "tu fais quoi", "presente toi"),
        "Je suis Helios, l'assistant énergie de la maison. Je réponds sur l'isolation, le "
        "chauffage, le solaire, les aides — et je relis les devis.",
    ),
)

#: Formulations qui varient trop pour une liste : « alloooo », « bonjouuur », « helloooo ».
_LETTRE_REPETEE = re.compile(r"(.)\1{2,}")

#: Au-delà, le message porte forcément autre chose qu'une politesse.
_MOTS_MAXI = 5


def normaliser(texte: str) -> str:
    """Minuscules, sans accent, sans ponctuation ni emoji, espaces resserrés.

    « Bonjour !! 👋 » et « bonjour » doivent tomber sur la même entrée. Le point
    d'interrogation est gardé : « ? » tout seul est un message à part entière.
    """
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte.lower())
        if unicodedata.category(c) != "Mn"
    )
    lettres = "".join(
        c if (c.isalnum() or c.isspace() or c == "?") else " " for c in sans_accent
    )
    if "?" not in lettres:
        # « alloooo » → « allo ». On épargne les « ??? », qui sont dans la liste tels quels.
        lettres = _LETTRE_REPETEE.sub(r"\1", lettres)
    return " ".join(lettres.split())


def repondre(texte: str) -> str | None:
    """La réponse écrite pour ce message, ou None s'il faut le traiter normalement."""
    normalise = normaliser(texte)
    if not normalise:
        return None

    if len(normalise.split()) > _MOTS_MAXI:
        return None

    # « bonjour ? » et « bonjour » sont le même message ; « ? » seul ne l'est pas.
    depouille = " ".join(normalise.replace("?", " ").split())

    for formulations, reponse in _CIVILITES:
        if normalise in formulations or (depouille and depouille in formulations):
            return reponse
    return None
