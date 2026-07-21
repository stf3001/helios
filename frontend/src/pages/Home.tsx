import { Link } from 'react-router-dom'
import { MessageSquare, ClipboardList, Sparkles, Gift, ShieldCheck, Lock, ArrowRight, Sun, BatteryCharging, Car, Droplets } from 'lucide-react'
import HierarchieColibri from '../components/HierarchieColibri'
import ScrollReveal from '../components/ScrollReveal'
import { useTitle } from '../hooks/useTitle'

const ETAPES = [
  { icon: ClipboardList, titre: 'Décrivez votre maison', desc: 'Année, surface, chauffage, isolation… Tout est optionnel et modifiable. Un score vous montre ce qui affine le diagnostic.' },
  { icon: Sparkles, titre: 'Helios analyse', desc: 'Points faibles probables, ordre de priorité des travaux, puis ordres de grandeur : économies, coûts, aides.' },
  { icon: MessageSquare, titre: 'Agissez à votre rythme', desc: 'Des gestes gratuits au gros chantier. Et si vous le voulez, une mise en relation avec un artisan de confiance.' },
]

const REASSURANCE = [
  { icon: Gift, titre: 'Gratuit, toujours', desc: 'Jamais facturé au client.' },
  { icon: ShieldCheck, titre: 'Indépendant', desc: 'Aucun produit à vous vendre.' },
  { icon: Lock, titre: 'Vos données protégées', desc: 'Export et suppression à tout moment.' },
]

export default function Home() {
  useTitle()
  return (
    <>
      {/* Héros */}
      <section className="relative overflow-hidden bg-gradient-to-br from-sun via-primary to-terra">
        <div className="max-w-[1100px] mx-auto px-4 py-16 md:py-20 grid md:grid-cols-[1.4fr_1fr] gap-8 items-center">
          <div className="text-white animate-slide-up">
            <h1 className="font-display text-4xl md:text-5xl font-bold leading-tight text-white">
              Votre maison mérite un conseil franc.
            </h1>
            <p className="text-lg text-white/90 mt-4 max-w-xl">
              Helios est une intelligence artificielle indépendante qui analyse votre logement et vous guide
              dans vos travaux d'énergie — gratuitement, sans rien à vous vendre, à votre rythme.
            </p>
            <div className="flex flex-wrap gap-3 mt-7">
              <Link to="/helios" className="inline-flex items-center gap-2 rounded-xl bg-white text-primary font-semibold px-5 py-3 hover:bg-white/90">
                <MessageSquare className="w-5 h-5" /> Poser ma question à Helios
              </Link>
              <Link to="/inscription" className="inline-flex items-center gap-2 rounded-xl bg-ink/20 text-white font-semibold px-5 py-3 hover:bg-ink/30 border border-white/30">
                Créer mon espace gratuit
              </Link>
            </div>
          </div>
          <div className="hidden md:flex justify-center">
            <img src="/brand/helios-salute.png" alt="Helios vous accueille" className="h-64 drop-shadow-xl" />
          </div>
        </div>
      </section>

      {/* Réassurance */}
      <section className="bg-cream border-b border-black/5">
        <div className="max-w-[1000px] mx-auto px-4 py-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {REASSURANCE.map((r) => (
            <div key={r.titre} className="flex items-center gap-3">
              <div className="shrink-0 w-10 h-10 rounded-xl bg-white flex items-center justify-center text-primary">
                <r.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="font-semibold text-ink text-sm">{r.titre}</div>
                <div className="text-xs text-gray-500">{r.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* La maison de demain */}
      <section className="max-w-[1000px] mx-auto px-4 py-16 text-center">
        <p className="uppercase tracking-widest text-primary text-sm font-semibold mb-3">La maison de demain</p>
        <h2 className="font-display text-2xl md:text-3xl font-bold text-ink mb-4">
          Pour la première fois, votre maison peut produire son énergie — et bien plus.
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto mb-8">
          Isolée, intelligente, capable de produire son électricité verte, de la stocker, de se chauffer,
          de recharger la voiture, et même de produire son eau. Ce n'était pas possible avant. Ça l'est aujourd'hui.
        </p>
        <div className="flex flex-wrap justify-center gap-3 mb-6">
          {[
            { icon: Sun, label: 'Produire' },
            { icon: BatteryCharging, label: 'Stocker' },
            { icon: Car, label: 'Se déplacer' },
            { icon: Droplets, label: 'Son eau', to: '/eau' },
          ].map((c) =>
            c.to ? (
              <Link key={c.label} to={c.to}
                className="inline-flex items-center gap-2 rounded-full bg-cream border border-black/5 px-4 py-2 text-sm text-ink hover:border-sky hover:text-sky transition">
                <c.icon className="w-4 h-4 text-primary" /> {c.label}
              </Link>
            ) : (
              <div key={c.label} className="inline-flex items-center gap-2 rounded-full bg-cream border border-black/5 px-4 py-2 text-sm text-ink">
                <c.icon className="w-4 h-4 text-primary" /> {c.label}
              </div>
            )
          )}
        </div>
        <div className="flex flex-wrap justify-center items-center gap-x-4 gap-y-2">
          <Link to="/vision" className="inline-flex items-center gap-1.5 text-primary font-semibold hover:gap-2.5 transition-all">
            Découvrir notre vision <ArrowRight className="w-4 h-4" />
          </Link>
          <span className="text-gray-300 hidden sm:inline">·</span>
          <Link to="/qui-sommes-nous" className="inline-flex items-center gap-1.5 text-primary font-semibold hover:gap-2.5 transition-all">
            Qui sommes-nous <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* 3 étapes */}
      <section className="max-w-[1100px] mx-auto px-4 py-16 bg-cream rounded-3xl">
        <h2 className="text-2xl md:text-3xl font-bold text-center mb-3">Comment ça marche</h2>
        <p className="text-center text-gray-600 mb-10">Trois étapes, à votre rythme — sans engagement.</p>
        <div className="grid gap-6 md:grid-cols-3">
          {ETAPES.map((e, i) => (
            <ScrollReveal key={e.titre} delay={i * 80} className="rounded-2xl border border-gray-200 p-6 bg-white">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-11 h-11 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                  <e.icon className="w-6 h-6" />
                </div>
                <span className="text-sm font-bold text-primary">Étape {i + 1}</span>
              </div>
              <h3 className="font-display font-semibold text-lg text-ink mb-1">{e.titre}</h3>
              <p className="text-sm text-gray-600">{e.desc}</p>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* Hiérarchie colibri */}
      <section className="bg-cream py-16">
        <div className="max-w-[900px] mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-2">Un conseil qui va dans le bon ordre</h2>
          <HierarchieColibri />
        </div>
      </section>

      {/* Esprit colibri */}
      <ScrollReveal as="section" className="max-w-[900px] mx-auto px-4 py-16 text-center">
        <p className="font-display text-2xl md:text-3xl font-semibold text-ink mb-3">« Je le sais, mais je fais ma part. »</p>
        <p className="text-gray-700 max-w-xl mx-auto">
          Chaque geste compte — pour la planète et pour votre facture. Un conseil gratuit qui fait économiser
          50&nbsp;€ vaut autant qu'un chantier à 30&nbsp;000&nbsp;€.
        </p>
        <Link to="/colibri" className="inline-flex items-center gap-1.5 text-primary font-semibold mt-4 hover:gap-2.5 transition-all">
          L'esprit colibri <ArrowRight className="w-4 h-4" />
        </Link>
      </ScrollReveal>

      {/* Transparence */}
      <ScrollReveal as="section" className="max-w-[900px] mx-auto px-4 pb-16">
        <div className="border-l-4 border-primary bg-cream rounded-r-2xl p-6 text-gray-700">
          <strong className="text-ink">Transparence.</strong> HELIOS est gratuit pour vous, toujours. La plateforme
          se rémunère par une commission versée par les entreprises partenaires quand vous leur confiez des travaux.
          Les conseils d'Helios sont strictement indépendants de ce mécanisme — c'est écrit dans{' '}
          <Link to="/engagements" className="underline hover:text-primary">sa charte</Link>, et c'est non négociable.
        </div>
      </ScrollReveal>

      {/* CTA final */}
      <section className="bg-ink text-white">
        <div className="max-w-[900px] mx-auto px-4 py-14 text-center">
          <h2 className="font-display text-2xl md:text-3xl font-bold text-white mb-3">Prêt à y voir clair ?</h2>
          <p className="text-white/80 mb-7">Posez une question, ou créez votre espace pour un conseil personnalisé. Gratuit, sans engagement.</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/helios" className="rounded-xl bg-primary text-white font-semibold px-6 py-3 hover:opacity-90">Parler à Helios</Link>
            <Link to="/inscription" className="rounded-xl bg-white/10 text-white font-semibold px-6 py-3 hover:bg-white/20 border border-white/20">Créer mon espace</Link>
          </div>
        </div>
      </section>
    </>
  )
}
