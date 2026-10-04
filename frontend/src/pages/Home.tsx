import { Link } from 'react-router-dom'
import {
  ArrowRight, BatteryCharging, Car, ClipboardList, Droplet, House,
  MessageSquare, Sparkles, Sprout, Sun, Wind,
} from 'lucide-react'
import CarteMaison from '../components/CarteMaison'
import HierarchieColibri from '../components/HierarchieColibri'
import ScrollReveal from '../components/ScrollReveal'
import HeroSearch from '../components/HeroSearch'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'

/** LA PHOTO DU HÉROS — un seul endroit à changer.
 *
 *  1536 × 1024 (3:2). C'est la proportion qui rend cette mise en page possible :
 *  un héros se taille entre 2:1 et 2,4:1, donc le recadrage ne coupe que du ciel
 *  en haut et de la terrasse en bas — **jamais la toiture solaire**, qui est le
 *  seul élément de l'image qui porte le propos.
 *
 *  Ses teintes SONT la charte : la tuile est le terracotta de la marque, les murs
 *  sont l'ivoire du site, la lumière de fin de journée est l'or du pied de page.
 *  D'où un raccord invisible avec le fond de la page.
 *
 *  **Limite connue** : 1536 px de large. Plein cadre sur un 1920 elle est agrandie
 *  1,25 fois, davantage sur un écran à forte densité. Une version plus large se
 *  déposerait ici sans toucher à la mise en page. */
const PHOTO = '/maison-hero.webp'

/** Les quatre portes d'entrée du site, dans l'ordre du menu. La première est la
 *  tuile sombre : c'est le sujet principal, et un seul aplat d'encre suffit à le
 *  dire — pas besoin d'un badge « populaire » par-dessus. */
const TUILES = [
  {
    to: '/simulateur-solaire', icon: House, titre: 'La maison de demain',
    desc: 'Solaire, isolation, chauffage : le bon ordre pour vos travaux.',
    sombre: true,
  },
  {
    to: '/le-vent', icon: Wind, titre: 'Le vent',
    desc: 'L’éolien vertical, pour qui et à quelles conditions.',
    teinte: 'text-sky',
  },
  {
    to: '/eau', icon: Droplet, titre: 'L’eau',
    desc: 'Récupérer, produire et économiser l’eau à la maison.',
    teinte: 'text-sky',
  },
  {
    to: '/la-terre', icon: Sprout, titre: 'La terre',
    desc: 'Géothermie et sols : ce que votre terrain peut offrir.',
    teinte: 'text-leaf',
  },
]

const ETAPES = [
  { icon: ClipboardList, titre: 'Décrivez votre maison', desc: 'Année, surface, chauffage, isolation… Tout est optionnel et modifiable. Un score vous montre ce qui affine le diagnostic.' },
  { icon: Sparkles, titre: 'Helios analyse', desc: 'Points faibles probables, ordre de priorité des travaux, puis ordres de grandeur : économies, coûts, aides.' },
  { icon: MessageSquare, titre: 'Agissez à votre rythme', desc: 'Des gestes gratuits au gros chantier. Et si vous le voulez, une mise en relation avec un artisan de confiance.' },
]

export default function Home() {
  useTitle()
  const { user } = useAuth()
  // Le carnet EST la fiche de maison : un visiteur connecté y va directement,
  // les autres passent par la création d'espace. Aucune route nouvelle.
  const versLeCarnet = user ? '/mon-espace' : '/inscription'

  return (
    <>
      {/* ---------------- HÉROS ----------------
          Helios est le sujet de la phrase, pas le visiteur : « la maison a enfin
          son expert » dit ce qu'EST le produit, là où « un logement que vous
          comprenez » décrivait un état d'esprit.

          LA PHOTO OCCUPE TOUT LE CADRE, ET LE VOILE N'A AUCUN PALIER.
          Les deux essais précédents ont échoué pour la même raison, en miroir :
          un voile opaque jusqu'à 55 %, puis une photo bornée à un bloc de 58 %,
          produisaient tous les deux DEUX ZONES au lieu d'une image — un aplat
          d'ivoire vide à gauche, une photo à droite, et une couture verticale
          entre les deux d'autant plus visible que l'écran est large.

          Le voile part donc du bord gauche et décroît sans interruption jusqu'à
          66 % : aucun segment d'opacité constante, donc aucune arête. On lit une
          brume, pas une découpe — c'est ce que fait la maquette d'origine, où le
          flanc gauche de la villa se dissout dans la crème.

          La lisibilité n'est plus affaire de géométrie mais de contraste, et elle
          est MESURÉE, pas supposée : les pixels réels de la photo sont échantillonnés
          sous chaque bloc de texte, composités avec l'alpha exact du dégradé à cette
          abscisse, et comparés à la couleur du texte (WCAG). C'est aussi pour cela
          que le sous-titre est en `text-ink/80` et non en `text-gray-600` : le gris
          secondaire demande un fond de luminance 0,61 pour tenir 4,5:1, ce que le
          flanc de colline ne donne pas. L'encre, elle, passe largement.

          DÉTAIL QUI A SON IMPORTANCE : le dégradé se termine sur
          `rgb(var(--h-sable) / 0)` et non sur `transparent`. En CSS `transparent`
          vaut `rgba(0,0,0,0)` : interpolé en sRGB, il tire le dégradé vers le NOIR
          et salit tout le raccord. C'est ce qui ternissait les essais précédents.

          Cadrage : photo en 3:2, héros en ~2,6:1 — on ne perd que du ciel en haut
          et la piscine en bas. `object-[center_30%]` garde la toiture solaire
          entière, seul élément de l'image qui porte le propos. */}
      <section className="relative overflow-hidden lg:min-h-[560px] lg:flex lg:items-center">
        {/* GRAND ÉCRAN SEULEMENT. En dessous de `lg` il n'y a qu'une colonne : une
            photo en fond derrière du texte y serait soit illisible, soit effacée
            par un voile — elle passe donc en bandeau plus bas, à sa vraie place. */}
        <div className="hidden lg:block absolute inset-0 select-none" aria-hidden="true">
          <img
            src={PHOTO}
            alt=""
            className="w-full h-full object-cover object-[center_30%]"
            loading="eager"
            decoding="async"
          />
          {/* Écrit en style plutôt qu'en classes arbitraires : il lui faut cinq
              arrêts précis, et c'est le seul endroit du site concerné. Toute
              modification de ces valeurs doit être REMESURÉE (voir en tête). */}
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to right,' +
                ' rgb(var(--h-sable) / 0.92) 0%,' +
                ' rgb(var(--h-sable) / 0.88) 28%,' +
                ' rgb(var(--h-sable) / 0.82) 46%,' +
                ' rgb(var(--h-sable) / 0.42) 58%,' +
                ' rgb(var(--h-sable) / 0.10) 70%,' +
                ' rgb(var(--h-sable) / 0) 80%)',
            }}
          />
        </div>

        {/* La colonne de texte est plus étroite à `lg` qu'à `xl` : à 1024 px, 500 px
            de texte représentent la moitié du cadre et débordent dans la partie du
            voile qui s'estompe (l'italique terracotta y tombait à 3,38:1, juste au
            seuil). À 440 px elle reste dans le plateau opaque. Sur grand écran le
            rapport est tout autre — 500 px ne font plus que le quart du cadre. */}
        <div className="relative w-full max-w-[1200px] mx-auto px-4 pt-12 pb-14 md:pt-16 lg:py-16 grid items-center gap-10 lg:grid-cols-[minmax(0,440px)_minmax(0,1fr)] xl:grid-cols-[minmax(0,500px)_minmax(0,1fr)] lg:gap-12 animate-slide-up">

          {/* --- Le propos ---
              TROIS LIGNES RETIRÉES le 02/10/2026, à la demande de Stéphane : la
              pastille « Gratuit · indépendant · vos données », la ligne « Énergie ·
              Travaux · Entretien · Équipements » et le lien « Pourquoi c'est
              gratuit ? ». Elles encadraient le titre de trois bandeaux de petit
              texte et noyaient l'action. Ce qu'elles disaient n'est pas perdu : la
              gratuité est passée DANS la phrase (« un agent IA gratuit »), les
              quatre domaines sont les quatre tuiles juste en dessous, et le modèle
              économique reste expliqué par le bloc « Transparence » plus bas, qui
              pointe toujours vers `/engagements`. */}
          <div className="text-center lg:text-left">
            <h1 className="font-display text-[44px] leading-[1.04] sm:text-6xl lg:text-[64px] lg:leading-[1.03] text-ink">
              La maison a enfin{' '}
              <em className="italic text-primary">son expert.</em>
            </h1>

            {/* `text-ink/80` et non `text-gray-600` : voir la note de contraste en
                tête de section. Le gris secondaire du site est calibré pour un fond
                ivoire, pas pour un flanc de colline vu à travers une brume. */}
            <p className="mt-6 text-lg text-ink/80 max-w-[460px] mx-auto lg:mx-0">
              Un agent IA gratuit qui connaît votre foyer, retient son histoire et
              l’accompagne dans le temps.
            </p>

            {/* UNE seule action. « Découvrir Helios » (l'intitulé de la maquette) ne
                promettait rien et n'engageait à rien ; « Décrire ma maison » dit ce
                que le clic fait, et répond au constat posé à côté. Le deuxième
                chemin, poser une question, a sa propre section juste en dessous. */}
            <div className="mt-8 flex justify-center lg:justify-start">
              <Link
                to={versLeCarnet}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary text-white font-semibold px-7 py-3.5 hover:bg-terra transition-colors"
              >
                Décrire ma maison <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </Link>
            </div>
          </div>

          {/* --- Le constat d'Helios ---
                  Étroit (300 px) et repoussé vers le bord droit (`xl:-mr-8`) : il
                  occupe la marge de la terrasse plutôt que le centre de l'image, et
                  laisse la façade, la toiture et les panneaux dégagés. Le décalage
                  n'est appliqué qu'à partir de `xl` — en dessous, la gouttière du
                  conteneur n'a pas de quoi l'absorber et la carte sortirait de
                  l'écran. Elle est plus HAUTE que l'ancienne alors qu'elle contient
                  moins : c'est le texte qui se replie dans une colonne étroite, et
                  une carte verticale se tient mieux contre le bord d'une photo. */}
          <div className="lg:justify-self-end lg:self-end xl:-mr-8 w-full max-w-[340px] lg:max-w-[300px] mx-auto lg:mx-0">
            {/* PETIT ÉCRAN. La photo en bandeau, pleine largeur, juste au-dessus du
                constat : on voit la maison, puis ce qu'Helios en sait. Le rapport
                3:2 est EXACTEMENT celui du fichier — donc aucun recadrage, la
                maison entière, qui était la remarque de Stéphane sur le 16:10. */}
            <img
              src={PHOTO}
              alt="Maison méditerranéenne en fin de journée, panneaux solaires sur la toiture."
              className="lg:hidden w-full aspect-[3/2] object-cover object-center rounded-2xl mb-5"
              loading="eager"
              decoding="async"
            />
            <CarteMaison />
          </div>
        </div>
      </section>

      {/* ---------------- ESSAYER AVANT DE SCROLLER ----------------
          La barre de question était DANS le héros, en action principale. Elle en
          sort pour lui laisser un seul geste, et garde sa place sur l'accueil à
          l'endroit juste : après la promesse et après sa démonstration.
          Promesse → preuve → essai, au lieu de trois choses qui se disputent le
          même écran. C'est aussi ce qui remplace la bulle de conversation de la
          maquette — en vrai, et branchée sur le chat. */}
      <section className="px-4 pt-12 pb-14 md:pb-16">
        <div className="max-w-[720px] mx-auto text-center">
          <h2 className="font-display text-2xl sm:text-3xl text-ink">
            Posez-lui n’importe quelle question sur votre maison.
          </h2>
          <div className="mt-6">
            <HeroSearch />
          </div>
        </div>
      </section>

      {/* ---------------- LES QUATRE PORTES ---------------- */}
      <section className="px-4 pb-16">
        <h2 className="sr-only">Les sujets d’Helios</h2>
        <div className="max-w-[1100px] mx-auto grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          {TUILES.map((t) => (
            <Link
              key={t.to}
              to={t.to}
              className={
                'group rounded-2xl border p-6 flex flex-col min-h-[180px] transition-colors ' +
                (t.sombre
                  ? 'bg-ink border-ink text-sable hover:bg-ink/90'
                  : 'bg-white border-bord hover:border-gray-300')
              }
            >
              <t.icon
                className={'w-6 h-6 mb-6 ' + (t.sombre ? 'text-sun' : t.teinte)}
                strokeWidth={1.5}
                aria-hidden="true"
              />
              <h3 className={'font-display text-xl ' + (t.sombre ? 'text-sable' : 'text-ink')}>
                {t.titre}
              </h3>
              <p className={'mt-2 text-sm ' + (t.sombre ? 'text-sable/75' : 'text-gray-600')}>
                {t.desc}
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* ---------------- LE CARNET DE MAISON ---------------- */}
      <section className="px-4 pb-20">
        <div className="max-w-[1100px] mx-auto rounded-2xl bg-cream px-6 py-8 sm:px-10 sm:py-9 flex flex-col sm:flex-row sm:items-center gap-6">
          <div className="flex-1">
            <h2 className="font-display text-2xl sm:text-3xl text-ink">Votre carnet de maison</h2>
            <p className="mt-2 text-gray-600 max-w-[620px]">
              Ce que vous dites à Helios ne se perd pas : année de construction, travaux
              déjà faits, devis relus, entretiens à venir. Il s’en souvient, et ses
              conseils s’affinent à mesure que le carnet se remplit.
            </p>
          </div>
          <Link
            to={versLeCarnet}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-ink/25 text-ink font-semibold px-6 py-3 shrink-0 hover:bg-ink hover:text-sable hover:border-ink transition-colors"
          >
            Découvrir <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      </section>

      {/* ---------------- LA MAISON DE DEMAIN (le propos) ---------------- */}
      <section className="max-w-[820px] mx-auto px-4 pb-20 text-center">
        <p className="uppercase tracking-[0.18em] text-primary text-xs font-semibold mb-4">La maison de demain</p>
        <h2 className="font-display text-3xl md:text-4xl text-ink mb-4 leading-tight">
          Pour la première fois, votre maison peut produire son énergie — et bien plus.
        </h2>
        <p className="text-gray-600 max-w-[620px] mx-auto mb-8">
          Isolée, intelligente, capable de produire son électricité verte, de la stocker, de se chauffer,
          de recharger la voiture, et même de produire son eau. Ce n'était pas possible avant. Ça l'est aujourd'hui.
        </p>
        <div className="flex flex-wrap justify-center gap-2.5 mb-8">
          {[
            { icon: Sun, label: 'Produire' },
            { icon: BatteryCharging, label: 'Stocker' },
            { icon: Car, label: 'Se déplacer' },
            { icon: Droplet, label: 'Son eau', to: '/eau' },
          ].map((c) =>
            c.to ? (
              <Link key={c.label} to={c.to}
                className="inline-flex items-center gap-2 rounded-full bg-white border border-bord px-4 py-2 text-sm text-ink hover:border-sky hover:text-sky transition-colors">
                <c.icon className="w-4 h-4 text-primary" strokeWidth={1.5} /> {c.label}
              </Link>
            ) : (
              <div key={c.label} className="inline-flex items-center gap-2 rounded-full bg-white border border-bord px-4 py-2 text-sm text-ink">
                <c.icon className="w-4 h-4 text-primary" strokeWidth={1.5} /> {c.label}
              </div>
            )
          )}
        </div>
        <div className="flex flex-wrap justify-center items-center gap-x-5 gap-y-2">
          <Link to="/vision" className="inline-flex items-center gap-1.5 text-primary font-semibold hover:gap-2.5 transition-all">
            Découvrir notre vision <ArrowRight className="w-4 h-4" />
          </Link>
          <span className="text-gray-300 hidden sm:inline" aria-hidden="true">·</span>
          <Link to="/qui-sommes-nous" className="inline-flex items-center gap-1.5 text-primary font-semibold hover:gap-2.5 transition-all">
            Qui sommes-nous <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ---------------- 3 ÉTAPES ---------------- */}
      <section className="px-4 pb-20">
        <div className="max-w-[1100px] mx-auto rounded-2xl bg-cream px-6 py-14 sm:px-10">
          <h2 className="font-display text-3xl md:text-4xl text-center mb-3">Comment ça marche</h2>
          <p className="text-center text-gray-600 mb-10">Trois étapes, à votre rythme.</p>
          <div className="grid gap-4 md:grid-cols-3">
            {ETAPES.map((e, i) => (
              <ScrollReveal key={e.titre} delay={i * 80} className="rounded-2xl border border-bord p-6 bg-white">
                <div className="flex items-center gap-3 mb-4">
                  <e.icon className="w-5 h-5 text-primary" strokeWidth={1.5} aria-hidden="true" />
                  <span className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Étape {i + 1}</span>
                </div>
                <h3 className="font-display text-xl text-ink mb-1.5">{e.titre}</h3>
                <p className="text-sm text-gray-600">{e.desc}</p>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- HIÉRARCHIE COLIBRI ---------------- */}
      <section className="pb-20">
        <div className="max-w-[900px] mx-auto px-4">
          <h2 className="font-display text-3xl md:text-4xl text-center mb-2">Un conseil qui va dans le bon ordre</h2>
          <HierarchieColibri />
        </div>
      </section>

      {/* ---------------- ESPRIT COLIBRI ---------------- */}
      <ScrollReveal as="section" className="max-w-[820px] mx-auto px-4 pb-20 text-center">
        <p className="font-display text-3xl md:text-4xl text-ink mb-4 leading-snug">
          « Je le sais, mais <em className="italic text-primary">je fais ma part.</em> »
        </p>
        <p className="text-gray-600 max-w-[560px] mx-auto">
          Chaque geste compte — pour la planète et pour votre facture. Un conseil gratuit qui fait économiser
          50&nbsp;€ vaut autant qu'un chantier à 30&nbsp;000&nbsp;€.
        </p>
        <Link to="/colibri" className="inline-flex items-center gap-1.5 text-primary font-semibold mt-5 hover:gap-2.5 transition-all">
          L'esprit colibri <ArrowRight className="w-4 h-4" />
        </Link>
      </ScrollReveal>

      {/* ---------------- TRANSPARENCE ---------------- */}
      <ScrollReveal as="section" className="max-w-[900px] mx-auto px-4 pb-20">
        <div className="border-l-2 border-primary bg-white border-y border-r border-bord rounded-r-2xl p-6 text-gray-600">
          <strong className="font-semibold text-ink">Transparence.</strong> HELIOS est gratuit pour vous, toujours. La plateforme
          se rémunère par une commission versée par les entreprises partenaires quand vous leur confiez des travaux.
          Les conseils d'Helios sont strictement indépendants de ce mécanisme — c'est écrit dans{' '}
          <Link to="/engagements" className="underline underline-offset-2 hover:text-primary">sa charte</Link>, et c'est non négociable.
        </div>
      </ScrollReveal>

      {/* ---------------- APPEL FINAL ---------------- */}
      <section className="bg-ink text-sable">
        <div className="max-w-[900px] mx-auto px-4 py-16 text-center">
          <h2 className="font-display text-3xl md:text-4xl text-sable mb-3">Prêt à y voir clair ?</h2>
          <p className="text-sable/75 mb-8">Posez une question, ou créez votre espace pour un conseil personnalisé. Gratuit, sans engagement.</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/helios" className="rounded-xl bg-primary text-white font-semibold px-6 py-3 hover:bg-terra transition-colors">Parler à Helios</Link>
            <Link to="/inscription" className="rounded-xl border border-sable/30 text-sable font-semibold px-6 py-3 hover:bg-sable/10 transition-colors">Créer mon espace</Link>
          </div>
        </div>
      </section>
    </>
  )
}
