import { Link } from 'react-router-dom'
import {
  ShieldCheck, Sun, BatteryCharging, Flame, Utensils, Car, Wifi, Droplets,
  Eye, HeartHandshake, Sparkles, Feather, ArrowRight,
} from 'lucide-react'
import { useTitle } from '../hooks/useTitle'
import ScrollReveal from '../components/ScrollReveal'
import CtaFaisTaPart from '../components/CtaFaisTaPart'

const CAPACITES = [
  { icon: ShieldCheck, titre: 'Bien isolée', desc: 'Elle garde sa chaleur l\'hiver, sa fraîcheur l\'été. Le socle de tout le reste.' },
  { icon: Sun, titre: 'Produit son énergie', desc: 'Le soleil sur son toit devient de l\'électricité verte, gratuite et locale.' },
  { icon: BatteryCharging, titre: 'La stocke', desc: 'Ce qu\'elle produit le jour, elle le garde pour la nuit. Plus autonome, moins dépendante.' },
  { icon: Flame, titre: 'Se chauffe proprement', desc: 'Pompe à chaleur, régulation fine : le confort sans le fioul ni le gaz.' },
  { icon: Utensils, titre: 'Cuit', desc: 'Cuisiner à l\'électricité produite sur place, sans énergie fossile.' },
  { icon: Car, titre: 'Se déplace', desc: 'La voiture se recharge au soleil du toit. La maison devient une station.' },
  { icon: Wifi, titre: 'Se connecte', desc: 'Pilotée intelligemment, elle optimise chaque kilowattheure, seule.' },
  { icon: Droplets, titre: 'Produit son eau', desc: 'Demain, capter l\'eau de l\'air ambiant. La maison devient une source.' },
]

const VALEURS = [
  { icon: Eye, titre: 'Transparence', desc: 'Notre modèle est affiché, nos préconisations expliquées. Jamais de boîte noire.' },
  { icon: HeartHandshake, titre: 'Honnêteté', desc: 'Si le meilleur conseil est « ne faites rien », Helios le dira. Des fourchettes, jamais de faux chiffres.' },
  { icon: Sparkles, titre: 'Excellence', desc: 'Une base de connaissances entretenue en continu, des sources fiables, des partenaires exigeants.' },
  { icon: Feather, titre: 'Humilité', desc: 'Helios oriente ; il ne remplace ni un audit réglementaire ni un professionnel. Il connaît ses limites.' },
]

export default function Vision() {
  useTitle('Notre vision')
  return (
    <>
      {/* Manifeste */}
      <section className="bg-gradient-to-br from-sun via-primary to-terra text-white">
        <div className="max-w-[900px] mx-auto px-4 py-20 text-center">
          <p className="uppercase tracking-widest text-white/80 text-sm mb-4">Notre vision</p>
          <h1 className="font-display text-4xl md:text-5xl font-bold text-white leading-tight">
            La maison de demain existe déjà. <br className="hidden md:block" />
            Aidons chaque foyer à la bâtir.
          </h1>
        </div>
      </section>

      {/* Le moment historique */}
      <section className="max-w-[820px] mx-auto px-4 py-16 space-y-5 text-lg text-gray-700">
        <p>
          Pour la <strong className="text-ink">première fois dans l'histoire de l'humanité</strong>, une maison
          ordinaire peut devenir presque autonome : bien isolée, intelligente, capable de
          <strong className="text-ink"> produire sa propre énergie verte, de la stocker</strong>, de se chauffer,
          de cuire, de recharger la voiture, de se piloter seule — et demain, de produire son eau.
        </p>
        <p>
          Ce n'était pas possible il y a vingt ans. Ça l'est aujourd'hui. Le solaire est abordable, le stockage
          arrive à maturité, l'intelligence artificielle sait enfin conseiller chacun selon son cas. Tous les
          morceaux existent — il manquait quelqu'un pour les assembler, honnêtement, autour de vous.
        </p>
      </section>

      {/* Les capacités de la maison de demain */}
      <section className="bg-cream py-16">
        <div className="max-w-[1100px] mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-3">Ce que votre maison peut devenir</h2>
          <p className="text-center text-gray-600 mb-10 max-w-xl mx-auto">
            Pas d'un coup, pas forcément tout — mais dans le bon ordre, à votre rythme et votre budget.
          </p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {CAPACITES.map((c, i) => (
              <ScrollReveal key={c.titre} delay={i * 60} className="bg-white rounded-2xl border border-gray-200 p-5">
                <div className="w-11 h-11 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-3">
                  <c.icon className="w-6 h-6" />
                </div>
                <h3 className="font-display font-semibold text-ink">{c.titre}</h3>
                <p className="text-sm text-gray-600 mt-1">{c.desc}</p>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Le problème + notre réponse */}
      <section className="max-w-[820px] mx-auto px-4 py-16 space-y-5 text-lg text-gray-700">
        <h2 className="text-2xl md:text-3xl font-bold text-ink">Alors pourquoi est-ce si compliqué ?</h2>
        <p>
          Parce que la transition est devenue un labyrinthe : aides qui changent chaque année, démarchage
          agressif, devis incompréhensibles, conseils orientés par celui qui vend. Résultat : des millions de
          foyers renoncent, ou se trompent de travaux.
        </p>
        <p>
          HELIOS, c'est <strong className="text-ink">l'alliance de l'expertise humaine et de l'intelligence
          artificielle</strong>, mise au service de cette vision. Un conseiller disponible à toute heure, qui
          connaît les normes et les aides, s'adapte à <em>votre</em> maison, <em>vos</em> objectifs, <em>votre</em>
          budget — et n'a rien à vous vendre. L'IA pour la puissance et la disponibilité ; l'humain pour le sens,
          l'exigence et le contrôle.
        </p>
      </section>

      {/* Les valeurs */}
      <section className="bg-cream py-16">
        <div className="max-w-[1000px] mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-10">Nos valeurs, non négociables</h2>
          <div className="grid gap-5 sm:grid-cols-2">
            {VALEURS.map((v, i) => (
              <ScrollReveal key={v.titre} delay={i * 60} className="bg-white rounded-2xl border border-gray-200 p-6 flex gap-4">
                <div className="shrink-0 w-11 h-11 rounded-xl bg-leaf/10 text-leaf flex items-center justify-center">
                  <v.icon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-display font-semibold text-lg text-ink">{v.titre}</h3>
                  <p className="text-sm text-gray-600 mt-1">{v.desc}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <ScrollReveal as="section" className="max-w-[820px] mx-auto px-4 py-16 text-center">
        <p className="font-display text-2xl md:text-3xl font-semibold text-ink mb-3">« Je le sais, mais je fais ma part. »</p>
        <p className="text-gray-700 max-w-xl mx-auto mb-6">
          La maison de demain se construit un geste après l'autre. Commençons par le vôtre.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link to="/helios" className="rounded-xl bg-primary text-white font-semibold px-6 py-3 hover:opacity-90">Parler à Helios</Link>
          <Link to="/colibri" className="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 text-ink font-semibold px-6 py-3 hover:bg-cream">
            L'esprit colibri <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/qui-sommes-nous" className="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 text-ink font-semibold px-6 py-3 hover:bg-cream">
            Qui sommes-nous <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </ScrollReveal>
    </>
  )
}
