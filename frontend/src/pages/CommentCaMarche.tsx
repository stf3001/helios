/**
 * « Qui est Helios ? » — la page qui présente le personnage, pas la mécanique.
 *
 * Elle s'appelait « Comment ça marche » et déroulait trois étapes numérotées. C'était
 * juste, et parfaitement froid : on y expliquait un processus à quelqu'un qui se demande
 * encore à qui il parle. La question qu'un visiteur se pose en arrivant n'est pas
 * « quelles sont les étapes », c'est « c'est quoi, ce truc, et pourquoi lui faire
 * confiance ». La page répond donc à celle-là, dans cet ordre.
 *
 * LE PERSONNAGE PORTE LA PAGE. Helios est en grand dans le bandeau, dans sa pose `hero`
 * — la plus ouverte, écrite pour ça et jamais utilisée jusqu'ici — et SON REGARD SUIT LE
 * POINTEUR. C'est ce qui fait la différence entre une illustration et quelqu'un : un
 * visiteur qui bouge sa souris voit les yeux le suivre, et comprend en une seconde qu'il
 * a affaire à un interlocuteur. Aucune image de stock ne produit cet effet-là.
 *
 * Les amorces de questions sont de VRAIS liens vers le chat, pré-remplis. Une fausse
 * conversation qui se tape toute seule ferait illusion deux secondes et mentirait sur ce
 * que l'outil sait faire ; un bouton qui pose réellement la question, non.
 */

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Check, MessageCircle, ShieldQuestion, Sparkles } from 'lucide-react'

import AvatarExpert from '../components/AvatarExpert'
import HeliosAvatar, { type HeliosPose, type HeliosState } from '../components/HeliosAvatar'
import RendezVousTel from '../components/RendezVousTel'
import HierarchieColibri from '../components/HierarchieColibri'
import MaisonDemain from '../components/MaisonDemain'
import { useTitle } from '../hooks/useTitle'

/**
 * Un Helios qui joue son geste QUAND ON ARRIVE SUR LUI, et pas au chargement de la page.
 *
 * Sans cela, le haussement d'épaules de « quand il ne sait pas » se jouait en haut de
 * page, pendant qu'on lisait le bandeau, et il était fini depuis longtemps quand le
 * lecteur arrivait enfin devant. Un geste que personne ne voit n'existe pas.
 *
 * L'observateur n'est pas débranché après le premier passage : on redescend, il rejoue.
 * C'est voulu — c'est ce qui donne l'impression que quelqu'un est là.
 */
function HeliosAuPassage({
  etat, hauteur, pose,
}: { etat: HeliosState; hauteur: number; pose?: HeliosPose }) {
  const boite = useRef<HTMLDivElement>(null)
  const [passages, setPassages] = useState(0)

  useEffect(() => {
    const el = boite.current
    if (!el) return
    const observateur = new IntersectionObserver(
      ([entree]) => { if (entree.isIntersecting) setPassages((n) => n + 1) },
      { threshold: 0.6 },
    )
    observateur.observe(el)
    return () => observateur.disconnect()
  }, [])

  return (
    <div ref={boite}>
      <HeliosAvatar state={passages ? etat : 'repos'} replay={passages}
        height={hauteur} restPose={pose} />
    </div>
  )
}

/**
 * L'ÉQUIPE — CONTENU PROVISOIRE, À REMPLACER AVANT TOUTE MISE EN LIGNE.
 *
 * Ces quatre personnes n'existent pas. Stéphane fournira les vraies fiches ; en attendant,
 * ces cartes tiennent la place et montrent la forme. Publier des biographies inventées
 * sous l'étiquette « notre équipe » tromperait le visiteur — et c'est précisément ce que
 * la charte interdit ailleurs sur ce site.
 *
 * Les portraits sont DESSINÉS et non photographiés : voir `AvatarExpert`. Le jour où les
 * vraies photos arrivent, on remplace l'avatar par une balise `img`, rien d'autre ne bouge.
 */
const EQUIPE = [
  {
    prenom: 'Camille', nom: 'R.', age: 41, secteur: 'Sud-Est',
    parcours: 'Ancienne conductrice de travaux en rénovation, passée au conseil après dix ans de chantiers.',
    anciennete: '8 ans de conseil aux particuliers en énergies renouvelables',
  },
  {
    prenom: 'Yanis', nom: 'B.', age: 35, secteur: 'Île-de-France',
    parcours: 'Thermicien de formation, il a dimensionné des installations solaires avant de les expliquer.',
    anciennete: '6 ans de conseil aux particuliers en énergies renouvelables',
  },
  {
    prenom: 'Hélène', nom: 'M.', age: 52, secteur: 'Grand Ouest',
    parcours: 'Vingt ans en maîtrise d’œuvre. Elle lit un devis comme d’autres lisent le journal.',
    anciennete: '12 ans de conseil aux particuliers en énergies renouvelables',
  },
  {
    prenom: 'Karim', nom: 'D.', age: 29, secteur: 'Nord et Est',
    parcours: 'Venu du dépannage chauffage, il connaît les pannes avant qu’on les décrive.',
    anciennete: '4 ans de conseil aux particuliers en énergies renouvelables',
  },
]

/** Vraies questions, vrais liens : elles ouvrent le chat avec la question déjà écrite. */
const AMORCES = [
  'Par quoi commencer pour isoler ma maison ?',
  'Ai-je intérêt à passer au solaire ?',
  'Ma facture a doublé, est-ce normal ?',
  'Ce devis de pompe à chaleur est-il correct ?',
]

function Amorce({ question }: { question: string }) {
  return (
    <Link
      to={`/helios?q=${encodeURIComponent(question)}`}
      className="group inline-flex items-center gap-2 rounded-full border border-white/40 bg-white/10
        px-4 py-2 text-sm text-white backdrop-blur transition hover:bg-white hover:text-primary"
    >
      {question}
      <ArrowRight className="h-4 w-4 shrink-0 transition group-hover:translate-x-0.5" />
    </Link>
  )
}

export default function CommentCaMarche() {
  useTitle('Qui est Helios ? — HELIOS')

  return (
    <>
      {/* ---------------- LE BANDEAU : la réponse en quatre lignes, et lui ---------------- */}
      <section className="hero-sunrise relative overflow-hidden">
        {/* Halo solaire derrière le personnage — le même souffle que le soleil du
            simulateur. Décoratif, donc invisible aux lecteurs d'écran. */}
        <div aria-hidden="true"
          className="pointer-events-none absolute -right-24 top-0 h-[36rem] w-[36rem] rounded-full
            bg-sun/25 blur-3xl md:right-0" />

        <div className="relative mx-auto grid max-w-[1100px] items-center gap-8 px-4 py-14
          md:grid-cols-[1.15fr_auto] md:py-16">
          <div>
            <h1 className="font-display text-4xl font-bold text-white md:text-5xl">
              Qui est Helios ?
            </h1>
            <div className="mt-5 space-y-2 text-lg text-white/95 md:text-xl">
              <p>
                Une intelligence artificielle qui ne s’intéresse qu’à une seule chose :
                <strong className="font-semibold"> votre logement</strong>.
              </p>
              <p>
                Posez-lui n’importe quelle question — chauffage, isolation, solaire,
                facture, devis.
              </p>
              <p>S’il ne sait pas, il vous le dira.</p>
              <p>S’il sait, il vous aidera à choisir.</p>
            </div>

            <div className="mt-7 flex flex-wrap gap-2">
              {AMORCES.slice(0, 3).map((q) => <Amorce key={q} question={q} />)}
            </div>
          </div>

          {/* Le personnage, en grand. `regard` est actif par défaut : ses yeux suivent
              le pointeur, et c'est tout l'effet recherché. */}
          <div className="hidden justify-self-center md:block">
            <HeliosAvatar state="repos" restPose="hero" height={360} />
          </div>
        </div>
      </section>

      {/* ---------------- CE QU'IL FAIT ---------------- */}
      <section className="mx-auto max-w-[1100px] px-4 py-14">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Il répond à tout ce qui touche votre maison
        </h2>
        <p className="mt-3 max-w-[760px] text-lg text-dark/80">
          Pas seulement à l’énergie. Une fenêtre qui siffle, une facture incompréhensible,
          un artisan qui ne rappelle pas, une aide dont vous ignorez si vous y avez droit :
          si ça concerne votre logement, c’est son sujet. Il ne vend rien, il n’a pas de
          quota, et personne ne le paie pour vous orienter quelque part.
        </p>

        <div className="mt-6 flex flex-wrap gap-2">
          {AMORCES.map((q) => (
            <Link key={q} to={`/helios?q=${encodeURIComponent(q)}`}
              className="group inline-flex items-center gap-2 rounded-full border border-ink/15
                bg-white px-4 py-2 text-sm text-ink transition hover:border-primary hover:text-primary">
              <MessageCircle className="h-4 w-4 shrink-0 text-primary" />
              {q}
              <ArrowRight className="h-4 w-4 shrink-0 opacity-0 transition group-hover:opacity-100" />
            </Link>
          ))}
        </div>
      </section>

      {/* ---------------- CE QU'IL FAIT QUAND IL NE SAIT PAS ---------------- */}
      <section className="bg-cream py-14">
        <div className="mx-auto grid max-w-[1100px] items-start gap-8 px-4 md:grid-cols-[auto_1fr]">
          {/* La pose « je ne sais pas » n'est pas un aveu de faiblesse ici : c'est
              l'argument. On la montre donc en grand, plutôt que de l'écrire — et elle se
              joue au moment où le lecteur arrive dessus. */}
          <div className="hidden justify-self-center md:block">
            <HeliosAuPassage etat="nesaitpas" hauteur={220} pose="salute" />
          </div>
          <div>
            <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
              Quand il ne sait pas, il le dit
            </h2>
            <p className="mt-3 text-lg text-dark/80">
              C’est la règle qui coûte le plus cher à tenir, et c’est celle qui fait la
              valeur du reste. Un assistant qui répond toujours quelque chose n’est utile
              nulle part : on ne peut plus distinguer ce qu’il sait de ce qu’il improvise.
            </p>
            <ul className="mt-5 space-y-3">
              {[
                ['Il annonce ses incertitudes', 'Des fourchettes et des ordres de grandeur, jamais un chiffre faussement précis.'],
                ['Il cite ses sources', 'Chaque réponse renvoie aux fiches sur lesquelles elle s’appuie. Vous pouvez vérifier.'],
                ['Il sait dire « ne faites rien »', 'Si le meilleur conseil est d’attendre, ou de commencer par un geste gratuit, c’est celui-là qu’il donne.'],
                ['Il se signale', 'Une réponse fausse ou gênante se signale en un clic, et elle est relue.'],
              ].map(([titre, texte]) => (
                <li key={titre} className="flex items-start gap-3">
                  <Check className="mt-1 h-5 w-5 shrink-0 text-leaf" />
                  <span className="text-dark/80">
                    <strong className="text-ink">{titre}</strong> — {texte}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ---------------- L'ESPACE : ce qui change quand il vous connaît ---------------- */}
      <section className="mx-auto max-w-[1100px] px-4 py-14">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Plus il connaît votre maison, plus ses réponses sont justes
        </h2>
        <p className="mt-3 max-w-[760px] text-lg text-dark/80">
          Sans compte, Helios répond déjà — mais à tout le monde pareil. En créant votre
          espace, il répond à <strong>vous</strong> : votre surface, votre chauffage, votre
          consommation, vos projets. C’est gratuit, et rien ne part chez personne sans votre
          accord.
        </p>

        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {[
            {
              icone: <Sparkles className="h-5 w-5 text-primary" />,
              titre: 'Vos études sont gardées',
              texte: 'Une simulation solaire, un devis relu, un diagnostic : vous les retrouvez, et Helios s’en sert pour la suite au lieu de repartir de zéro.',
            },
            {
              icone: <MessageCircle className="h-5 w-5 text-primary" />,
              titre: 'Vous complétez votre maison quand vous voulez',
              texte: 'Pièce par pièce, à votre rythme. Rien n’est obligatoire — chaque information rendue le rend simplement plus précis.',
            },
            {
              icone: <ShieldQuestion className="h-5 w-5 text-primary" />,
              titre: 'Vous lui parlez de n’importe quel sujet',
              texte: 'Travaux, factures, aides, artisans, projets à trois ans : tout ce qui concerne votre foyer, dans une conversation qui se souvient.',
            },
          ].map((bloc) => (
            <div key={bloc.titre} className="rounded-2xl border border-ink/10 bg-white p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                {bloc.icone}
              </div>
              <h3 className="mt-3 font-display text-lg font-bold text-ink">{bloc.titre}</h3>
              <p className="mt-1.5 text-dark/75">{bloc.texte}</p>
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Link to="/inscription"
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 font-semibold
              text-white transition hover:bg-primary/90">
            Créer mon espace gratuit <ArrowRight className="h-5 w-5" />
          </Link>
          <Link to="/helios" className="font-semibold text-ink underline hover:text-primary">
            ou lui poser une question tout de suite
          </Link>
        </div>
      </section>

      {/* ---------------- QUAND IL FAUT DU FORMEL, ET QUAND IL FAUT QUELQU'UN ---------------- */}
      <section className="bg-cream py-14">
        <div className="mx-auto max-w-[1100px] px-4">
          <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
            Et quand une machine ne suffit pas
          </h2>
          <p className="mt-3 max-w-[760px] text-lg text-dark/80">
            Il y a deux moments où Helios s’efface. Quand il faut un document
            <strong> officiel</strong> — pour une vente, une location, un dossier d’aide —
            il vous oriente vers un <strong>DPE</strong> réalisé par un diagnostiqueur
            certifié, et vous indique des professionnels si vous n’en connaissez pas. Et
            quand la question demande une vraie conversation, vous prenez trente minutes
            au téléphone avec quelqu’un de notre équipe.
          </p>

          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {EQUIPE.map((membre, i) => (
              <div key={membre.prenom} className="rounded-2xl border border-ink/10 bg-white p-5">
                <AvatarExpert variante={i} taille={72} className="rounded-full" />
                <h3 className="mt-3 font-display text-lg font-bold text-ink">
                  {membre.prenom} {membre.nom}
                </h3>
                <p className="text-sm text-dark/60">{membre.age} ans · {membre.secteur}</p>
                <p className="mt-2 text-sm text-dark/80">{membre.parcours}</p>
                <p className="mt-2 text-sm font-semibold text-primary">{membre.anciennete}</p>
              </div>
            ))}
          </div>

          <h3 className="mt-10 font-display text-xl font-bold text-ink">
            Réserver trente minutes au téléphone
          </h3>
          <p className="mb-4 mt-1 max-w-[760px] text-dark/75">
            Gratuit, sans engagement, et avec un être humain. Choisissez le moment qui vous
            arrange — on vous rappelle.
          </p>
          <div className="max-w-[820px]">
            <RendezVousTel />
          </div>
        </div>
      </section>

      {/* ---------------- LA MAISON DE DEMAIN ---------------- */}
      <section className="py-14">
        <div className="mx-auto max-w-[1100px] px-4">
          <h2 className="text-center font-display text-2xl font-bold text-ink md:text-3xl">
            Ce vers quoi il vous emmène
          </h2>
          <p className="mx-auto mb-6 mt-2 max-w-[640px] text-center text-dark/75">
            Une maison où l’énergie circule au bon moment, entre ce qu’elle produit, ce
            qu’elle stocke et ce qu’elle consomme. On n’y arrive pas d’un coup : Helios
            vous y conduit un geste à la fois, en commençant par ceux qui ne coûtent rien.
          </p>
          <MaisonDemain />
          <p className="mx-auto mt-3 max-w-[720px] text-center text-xs text-dark/60">
            Illustration de la vision d’ensemble. Certains éléments sont accessibles dès
            aujourd’hui (solaire, stockage, pilotage, eau atmosphérique via nos partenaires) ;
            d’autres, comme l’éolien domestique, arriveront progressivement. Helios ne vous
            propose jamais un équipement qui ne servirait pas réellement votre foyer.
          </p>
        </div>
      </section>

      {/* ---------------- LA HIÉRARCHIE QUI GUIDE CHAQUE CONSEIL ---------------- */}
      <section className="mx-auto max-w-[900px] px-4 py-14">
        <h2 className="mb-2 text-center font-display text-2xl font-bold text-ink md:text-3xl">
          Dans quel ordre il raisonne
        </h2>
        <p className="mx-auto mb-6 max-w-[640px] text-center text-dark/75">
          Toujours le même, et il ne s’en écarte pas : ce qui ne coûte rien d’abord, ce qui
          se vend en dernier.
        </p>
        <HierarchieColibri />
      </section>

      {/* ---------------- LA LIMITE, ANNONCÉE ---------------- */}
      <section className="mx-auto max-w-[900px] px-4 pb-14">
        <div className="rounded-r-2xl border-l-4 border-primary bg-cream p-6 text-dark/80">
          Le pré-diagnostic Helios est indicatif : il ne remplace pas un audit énergétique
          réglementaire réalisé par un professionnel certifié. Il vous aide à le préparer —
          et à le comprendre.
        </div>
      </section>
    </>
  )
}
