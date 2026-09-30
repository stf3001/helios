import { Link } from 'react-router-dom'
import {
  ArrowRight, BatteryCharging, Car, ClipboardList, Droplet, House,
  MessageSquare, Sparkles, Sprout, Sun, Wind,
} from 'lucide-react'
import HierarchieColibri from '../components/HierarchieColibri'
import ScrollReveal from '../components/ScrollReveal'
import HeroSearch from '../components/HeroSearch'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'

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
          On ouvre sur le bénéfice (comprendre son logement, être accompagné dans la
          durée), pas sur ce qu'Helios ne fait pas. La gratuité et l'indépendance
          deviennent un socle discret, posé en badge au-dessus du titre. */}
      <section className="px-4 pt-14 pb-12 md:pt-20 md:pb-16">
        <div className="max-w-[820px] mx-auto text-center animate-slide-up">
          {/* `items-start` et non `items-center` : sur un telephone la phrase passe a
              la ligne, et une pastille centree sur deux lignes tombe entre les deux.
              Elle s'aligne donc sur la PREMIERE ligne, quelle que soit la largeur. */}
          <p className="inline-flex items-start gap-2 rounded-full bg-cream px-4 py-1.5 text-[13px] leading-relaxed text-gray-600">
            <span className="mt-[0.5em] w-2 h-2 rounded-full bg-leaf shrink-0" aria-hidden="true" />
            <span>Gratuit · indépendant · vos données sous votre contrôle</span>
          </p>

          <h1 className="mt-7 font-display text-[44px] leading-[1.04] sm:text-6xl lg:text-[84px] lg:leading-[1.02] text-ink">
            Enfin, un logement{' '}
            <em className="italic text-primary">que vous comprenez.</em>
          </h1>

          <p className="mt-6 text-lg text-gray-600 max-w-[560px] mx-auto">
            Helios analyse votre maison, retient son histoire et vous accompagne
            dans la durée — travaux, entretien, énergie.
          </p>

          <div className="mt-9 max-w-[620px] mx-auto">
            <HeroSearch />
          </div>

          <p className="mt-6 text-sm">
            <Link to="/inscription" className="text-gray-600 underline underline-offset-4 hover:text-primary">
              Ou créez votre espace et décrivez votre maison
            </Link>
          </p>
          <p className="mt-2 text-[13px] text-gray-500">
            <Link to="/engagements" className="underline underline-offset-4 hover:text-primary">
              Pourquoi c’est gratuit ?
            </Link>
          </p>
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
