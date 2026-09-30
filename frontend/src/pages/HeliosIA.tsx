/**
 * « Helios » — la page unique du personnage ET de la conversation.
 *
 * Elle fusionne, le 30/09/2026, « Qui est Helios ? » (`/comment-ca-marche`) et
 * « Helios (IA) » (`/helios`). Les deux disaient la même chose à deux endroits du menu :
 * l'une présentait le personnage sans permettre de lui parler, l'autre donnait le champ
 * de saisie sans dire à qui on s'adresse. `/comment-ca-marche` redirige désormais ici.
 *
 * L'ORDRE EST LE POINT : le bandeau présente, la CONVERSATION VIENT TOUT DE SUITE APRÈS,
 * et la doctrine se lit ensuite. Un visiteur ne doit jamais traverser une page
 * d'explications pour atteindre le champ de saisie — c'est ce pour quoi il est venu.
 *
 * LE BANDEAU DIT QUI IL EST, EN TEXTE. La mascotte casquée a été retirée le 30/09/2026 :
 * ce qui distingue Helios n'est pas un personnage dessiné mais ce qu'il s'engage à faire,
 * et c'est cela que le bandeau met en avant.
 *
 * Les amorces sont de VRAIES questions : elles remplissent le champ juste en dessous,
 * l'utilisateur relit et envoie. Une fausse conversation qui se taperait toute seule
 * ferait illusion deux secondes et mentirait sur ce que l'outil sait faire.
 */

import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, Ban, Check, MessageCircle, ShieldQuestion, Sparkles } from 'lucide-react'

import AvatarExpert from '../components/AvatarExpert'
import ChatWidget from '../components/chat/ChatWidget'
import MarqueHelios from '../components/MarqueHelios'
import HierarchieColibri from '../components/HierarchieColibri'
import MaisonDemain from '../components/MaisonDemain'
import RendezVousTel from '../components/RendezVousTel'
import { useTitle } from '../hooks/useTitle'

/**
 * L'ÉQUIPE — CONTENU PROVISOIRE, À REMPLACER AVANT TOUTE MISE EN LIGNE.
 *
 * Ces quatre personnes n'existent pas. Stéphane fournira les vraies fiches ; en attendant,
 * ces cartes tiennent la place et montrent la forme. Publier des biographies inventées
 * sous l'étiquette « notre équipe » tromperait le visiteur — et c'est précisément ce que
 * la charte interdit ailleurs sur ce site. Voir le point 4 de TODO.md.
 */
const EQUIPE = [
  {
    prenom: 'Camille', nom: 'R.', age: 41, secteur: 'Sud-Est',
    parcours: 'Ancienne conductrice de travaux en rénovation, passée au conseil après dix ans de chantiers.',
    anciennete: '8 ans de conseil en énergies renouvelables',
  },
  {
    prenom: 'Yanis', nom: 'B.', age: 35, secteur: 'Île-de-France',
    parcours: 'Thermicien de formation, il a dimensionné des installations solaires avant de les expliquer.',
    anciennete: '6 ans de conseil en énergies renouvelables',
  },
  {
    prenom: 'Hélène', nom: 'M.', age: 52, secteur: 'Grand Ouest',
    parcours: 'Vingt ans en maîtrise d’œuvre. Elle lit un devis comme d’autres lisent le journal.',
    anciennete: '12 ans de conseil en énergies renouvelables',
  },
  {
    prenom: 'Karim', nom: 'D.', age: 29, secteur: 'Nord et Est',
    parcours: 'Venu du dépannage chauffage, il connaît les pannes avant qu’on les décrive.',
    anciennete: '4 ans de conseil en énergies renouvelables',
  },
]

/** Le contrat, en deux colonnes compactes : ce qu'il fait, ce qu'il ne fera jamais. */
const CONTRAT = [
  {
    icone: <Check className="h-4 w-4 text-leaf" />, titre: 'Ce qu’Helios fait',
    accent: 'border-leaf/30',
    points: [
      'Répond sur l’énergie, les travaux, les aides',
      'Analyse votre logement et priorise vos gestes',
      'Estime coûts, économies et aides en ordres de grandeur',
      'Vous oriente vers un professionnel certifié si besoin',
    ],
  },
  {
    icone: <Ban className="h-4 w-4 text-primary" />, titre: 'Ce qu’il ne fait jamais',
    accent: 'border-primary/30',
    points: [
      'Vendre, ou survendre quoi que ce soit',
      'Donner un chiffre certain là où il y a un doute',
      'Proposer un partenaire sans votre accord',
      'Se faire passer pour un audit réglementaire',
    ],
  },
]

export default function HeliosIA() {
  useTitle('Helios — l’IA au service de votre foyer | HELIOS')

  /* ?q= : arrivée depuis le champ de saisie de l'accueil → question pré-remplie, que
     l'utilisateur relit et envoie lui-même. L'effet compte : depuis la fusion, on est
     déjà sur cette page quand on repasse par la recherche de l'accueil, donc le
     composant n'est pas remonté et la seule valeur initiale ne suffirait pas. */
  const [searchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const [question, setQuestion] = useState(q)
  useEffect(() => { if (q) setQuestion(q) }, [q])

  return (
    <>
      {/* ---------------- LE BANDEAU : qui il est, et lui ---------------- */}
      <section className="border-b border-bord">
        <div className="mx-auto max-w-[900px] px-4 py-14 text-center md:py-16">
          <MarqueHelios taille={40} className="mx-auto mb-6 text-primary" />
          <h1 className="font-display text-4xl leading-[1.08] text-ink md:text-5xl lg:text-[56px]">
            Qui est <em className="italic text-primary">Helios</em> ?
          </h1>
          <div className="mx-auto mt-6 max-w-[620px] space-y-2 text-lg text-gray-600">
            <p>
              Une intelligence artificielle qui ne s’intéresse qu’à une seule chose :
              <strong className="font-semibold text-ink"> votre logement</strong>.
            </p>
            <p>Chauffage, isolation, solaire, facture, devis — posez votre question.</p>
            <p>S’il ne sait pas, il vous le dira. S’il sait, il vous aidera à choisir.</p>
          </div>
          <p className="mx-auto mt-5 max-w-[620px] text-sm text-gray-500">
            Sa particularité n’est pas sa technologie, mais sa constitution : des règles
            et des valeurs — transparence, humilité, honnêteté, excellence.
          </p>
        </div>
      </section>

      {/* ---------------- LA CONVERSATION, TOUT DE SUITE ----------------

          PAS D'AMORCES ICI : le widget porte déjà les siennes, dans la conversation,
          et elles s'effacent dès qu'on lui a parlé. Une deuxième série en dessous
          répétait les mêmes questions avec un comportement différent — les unes
          envoyaient, les autres remplissaient le champ. Un seul jeu, dans le widget. */}
      <section className="mx-auto max-w-[900px] px-4 pt-10">
        <ChatWidget initialInput={question || undefined} />
      </section>

      {/* ---------------- LE CONTRAT, EN PETIT ---------------- */}
      <section className="mx-auto max-w-[900px] px-4 py-10">
        <div className="grid gap-4 md:grid-cols-2">
          {CONTRAT.map((bloc) => (
            <div key={bloc.titre}
              className={`rounded-xl border bg-white p-4 ${bloc.accent}`}>
              <h2 className="flex items-center gap-2 font-display text-base font-bold text-ink">
                {bloc.icone}{bloc.titre}
              </h2>
              <ul className="mt-2 space-y-1 text-sm text-dark/75">
                {bloc.points.map((p) => (
                  <li key={p} className="flex gap-1.5">
                    <span aria-hidden="true" className="text-dark/30">·</span>{p}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- QUAND IL NE SAIT PAS ---------------- */}
      <section className="bg-cream py-12">
        <div className="mx-auto grid max-w-[1100px] items-center gap-8 px-4 md:grid-cols-[auto_1fr]">
          {/* « Je ne sais pas » n'est pas un aveu de faiblesse ici : c'est l'argument.
              La phrase est donc citée, en grand, plutôt qu'illustrée. */}
          <div className="hidden justify-self-center md:block">
            <p className="flex h-44 w-64 items-center justify-center rounded-2xl border border-bord
              bg-white px-6 text-center font-display text-3xl leading-snug text-ink">
              « Je ne sais&nbsp;<em className="italic text-primary">pas.</em> »
            </p>
          </div>
          <div>
            <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
              Quand il ne sait pas, il le dit
            </h2>
            <p className="mt-2 text-dark/80">
              C’est la règle qui coûte le plus cher à tenir, et c’est celle qui fait la
              valeur du reste. Un assistant qui répond toujours quelque chose n’est utile
              nulle part : on ne peut plus distinguer ce qu’il sait de ce qu’il improvise.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {[
                ['Il annonce ses incertitudes', 'Des fourchettes, jamais un chiffre faussement précis.'],
                ['Il cite ses sources', 'Chaque réponse renvoie aux fiches qui la fondent.'],
                ['Il sait dire « ne faites rien »', 'Si le bon conseil est d’attendre, c’est celui-là qu’il donne.'],
                ['Il se signale', 'Une réponse fausse se signale en un clic, et elle est relue.'],
              ].map(([titre, texte]) => (
                <div key={titre} className="rounded-xl border border-ink/10 bg-white p-3.5">
                  <p className="flex items-start gap-2 font-semibold text-ink">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-leaf" />{titre}
                  </p>
                  <p className="mt-1 text-sm text-dark/75">{texte}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- L'ESPACE : ce qui change quand il vous connaît ---------------- */}
      <section className="mx-auto max-w-[1100px] px-4 py-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Plus il connaît votre maison, plus ses réponses sont justes
        </h2>
        <p className="mt-2 max-w-[760px] text-dark/80">
          Sans compte, Helios répond déjà — mais à tout le monde pareil. En créant votre
          espace, il répond à <strong>vous</strong> : votre surface, votre chauffage, votre
          consommation, vos projets. C’est gratuit, et rien ne part chez personne sans votre
          accord.
        </p>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {[
            {
              icone: <Sparkles className="h-4 w-4 text-primary" />,
              titre: 'Vos études sont gardées',
              texte: 'Une simulation, un devis relu, un diagnostic : vous les retrouvez, et Helios s’en sert au lieu de repartir de zéro.',
            },
            {
              icone: <MessageCircle className="h-4 w-4 text-primary" />,
              titre: 'Vous complétez à votre rythme',
              texte: 'Pièce par pièce. Rien n’est obligatoire — chaque information le rend simplement plus précis.',
            },
            {
              icone: <ShieldQuestion className="h-4 w-4 text-primary" />,
              titre: 'Une conversation qui se souvient',
              texte: 'Travaux, factures, aides, artisans, projets à trois ans : tout ce qui concerne votre foyer.',
            },
          ].map((bloc) => (
            <div key={bloc.titre} className="rounded-xl border border-ink/10 bg-white p-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                {bloc.icone}
              </div>
              <h3 className="mt-2.5 font-display text-base font-bold text-ink">{bloc.titre}</h3>
              <p className="mt-1 text-sm text-dark/75">{bloc.texte}</p>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <Link to="/inscription"
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 font-semibold
              text-white transition hover:bg-primary/90">
            Créer mon espace gratuit <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* ---------------- QUAND IL FAUT DU FORMEL, ET QUAND IL FAUT QUELQU'UN ---------------- */}
      <section className="bg-cream py-12">
        <div className="mx-auto max-w-[1100px] px-4">
          <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
            Et quand une machine ne suffit pas
          </h2>
          <p className="mt-2 max-w-[760px] text-dark/80">
            Il y a deux moments où Helios s’efface. Quand il faut un document
            <strong> officiel</strong> — pour une vente, une location, un dossier d’aide —
            il vous oriente vers un <strong>DPE</strong> réalisé par un diagnostiqueur
            certifié, et vous indique des professionnels si vous n’en connaissez pas. Et
            quand la question demande une vraie conversation, vous prenez trente minutes
            au téléphone avec quelqu’un de notre équipe.
          </p>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {EQUIPE.map((membre, i) => (
              <div key={membre.prenom} className="rounded-xl border border-ink/10 bg-white p-4">
                <AvatarExpert variante={i} taille={56} className="rounded-full" />
                <h3 className="mt-2.5 font-display text-base font-bold text-ink">
                  {membre.prenom} {membre.nom}
                </h3>
                <p className="text-xs text-dark/60">{membre.age} ans · {membre.secteur}</p>
                <p className="mt-1.5 text-sm text-dark/80">{membre.parcours}</p>
                <p className="mt-1.5 text-xs font-semibold text-primary">{membre.anciennete}</p>
              </div>
            ))}
          </div>

          <h3 className="mt-8 font-display text-xl font-bold text-ink">
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

      {/* ---------------- DANS QUEL ORDRE IL RAISONNE ---------------- */}
      <section className="mx-auto max-w-[900px] px-4 py-12">
        <h2 className="mb-1.5 text-center font-display text-2xl font-bold text-ink md:text-3xl">
          Dans quel ordre il raisonne
        </h2>
        <p className="mx-auto mb-5 max-w-[640px] text-center text-dark/75">
          Toujours le même, et il ne s’en écarte pas : ce qui ne coûte rien d’abord, ce qui
          se vend en dernier.
        </p>
        <HierarchieColibri />
      </section>

      {/* ---------------- LA MAISON DE DEMAIN ---------------- */}
      <section className="pb-12">
        <div className="mx-auto max-w-[1100px] px-4">
          <h2 className="text-center font-display text-2xl font-bold text-ink md:text-3xl">
            Ce vers quoi il vous emmène
          </h2>
          <p className="mx-auto mb-5 mt-1.5 max-w-[640px] text-center text-dark/75">
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

      {/* ---------------- LA LIMITE, ANNONCÉE ---------------- */}
      <section className="mx-auto max-w-[900px] px-4 pb-14">
        <div className="rounded-r-2xl border-l-4 border-primary bg-cream p-5 text-sm text-dark/80">
          Le pré-diagnostic Helios est indicatif : il ne remplace pas un audit énergétique
          réglementaire réalisé par un professionnel certifié. Il vous aide à le préparer —
          et à le comprendre.
        </div>
      </section>
    </>
  )
}
