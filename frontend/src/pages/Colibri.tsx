import { Thermometer, Home, Sun, Sliders, Droplet } from 'lucide-react'
import Hero from '../components/Hero'
import ScrollReveal from '../components/ScrollReveal'
import CtaFaisTaPart from '../components/CtaFaisTaPart'
import { useTitle } from '../hooks/useTitle'

// Chiffres par foyer : repris tels quels de la base de connaissances d'Helios
// (mêmes fiches que la FAQ/le chat) — jamais un total agrégé inventé (doc 03).
const GESTES = [
  {
    icon: Thermometer,
    titre: 'Un thermostat bien réglé',
    texte: '1 °C de moins, c\'est environ 7 % de consommation de chauffage en moins. Gratuit et immédiat.',
  },
  {
    icon: Home,
    titre: 'Des combles isolés',
    texte: 'Le chantier au meilleur rapport coût/efficacité : souvent amorti en moins de 5 ans.',
  },
  {
    icon: Sun,
    titre: 'Un panneau solaire',
    texte: 'Bien dimensionné, il couvre une part réelle de votre consommation — pas plus, pas moins que nécessaire.',
  },
  {
    icon: Sliders,
    titre: 'Un pilotage intelligent',
    texte: 'Décaler ses usages vers les heures solaires peut faire passer l\'autoconsommation de 30 % à 50-70 %, sans rien acheter.',
  },
]

export default function Colibri() {
  useTitle("L'esprit colibri")
  return (
    <>
      <Hero title="L'esprit colibri" subtitle="Chaque geste compte pour construire un avenir durable." />

      {/* La légende */}
      <section className="max-w-[800px] mx-auto px-4 py-16">
        <ScrollReveal className="bg-gray-50 rounded-2xl p-6 md:p-8">
          <p className="text-lg text-gray-700 mb-4 italic">
            Un jour, dit la légende, il y eut un immense incendie de forêt. Tous les animaux, terrifiés,
            observaient impuissants le désastre. Seul le petit colibri s'activait, allant chercher
            quelques gouttes d'eau avec son bec pour les jeter sur le feu.
          </p>
          <p className="text-lg text-gray-700 mb-4 italic">
            Après un moment, le tatou, agacé par cette agitation dérisoire, lui dit : « Colibri ! Tu n'es
            pas fou ? Ce n'est pas avec ces gouttes d'eau que tu vas éteindre le feu ! »
          </p>
          <p className="text-lg text-gray-700 italic">
            Et le colibri lui répondit : « Je le sais, mais je fais ma part. »
          </p>
        </ScrollReveal>
        <ScrollReveal delay={100} className="mt-6 border-l-4 border-primary bg-primary/5 rounded-r-2xl p-5">
          <p className="text-sm text-gray-700">
            Cette légende amérindienne, popularisée par Pierre Rabhi, dit l'essentiel : chaque action
            individuelle, aussi modeste soit-elle, contribue à un changement collectif. On n'a pas besoin
            d'être parfait — seulement de faire sa part.
          </p>
        </ScrollReveal>
      </section>

      {/* Notre interprétation */}
      <section className="bg-cream py-16">
        <div className="max-w-[1000px] mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-3">Notre interprétation</h2>
          <p className="text-center text-gray-600 max-w-2xl mx-auto mb-10">
            Chez Helios, l'esprit colibri s'applique à l'énergie de votre logement. Aucun geste
            n'est trop petit — et Helios est là pour vous aider à choisir le vôtre.
          </p>
          <div className="grid gap-5 sm:grid-cols-2">
            {GESTES.map((g, i) => (
              <ScrollReveal key={g.titre} delay={i * 80} className="bg-white rounded-2xl border border-gray-200 p-5">
                <div className="w-11 h-11 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-3">
                  <g.icon className="w-6 h-6" />
                </div>
                <h3 className="font-display font-semibold text-ink">{g.titre}</h3>
                <p className="text-sm text-gray-600 mt-1">{g.texte}</p>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* L'effet collectif — honnête, sans chiffre inventé */}
      <section className="max-w-[820px] mx-auto px-4 py-16 space-y-5">
        <ScrollReveal>
          <h2 className="text-2xl md:text-3xl font-bold text-ink mb-4">Et à grande échelle ?</h2>
          <p className="text-lg text-gray-700">
            Helios ne prétend pas éteindre seul l'incendie climatique — et se méfie des grands chiffres
            ronds qui impressionnent sans rien prouver. Ce qu'on sait, c'est ceci : un foyer qui isole ses
            combles, c'est une chaudière moins sollicitée pendant vingt ans. Un foyer qui pilote son
            solaire, c'est un peu moins de réseau à renforcer. Mille foyers qui font ce choix, c'est un
            quartier qui respire différemment.
          </p>
          <p className="text-lg text-gray-700 mt-4">
            On ne vous donnera jamais un total nombre de tonnes de CO2 « évitées » — personne ne peut le
            mesurer sérieusement à cette échelle. Ce qu'on peut vous garantir, c'est que <strong className="text-ink">
            votre geste, lui, est réel</strong> : chiffré, vérifié, jamais gonflé.
          </p>
        </ScrollReveal>
      </section>

      {/* Rejoindre le mouvement */}
      <section className="bg-cream py-16">
        <div className="max-w-[1000px] mx-auto px-4">
          <div className="flex flex-col items-center text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-dark mb-3">Faites votre part</h2>
            <p className="text-lg text-gray-700 max-w-2xl mx-auto">
              Comme le colibri, vous pouvez commencer petit. Voici deux façons de faire la vôtre.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 gap-5 max-w-3xl mx-auto">
            <ScrollReveal className="bg-white rounded-2xl p-6">
              <h3 className="font-display font-semibold text-ink mb-2">Commencer chez vous</h3>
              <p className="text-sm text-gray-600 mb-4">
                Créez votre fiche maison, discutez avec Helios, et avancez à votre rythme — sobriété,
                isolation, systèmes, puis production. Un geste après l'autre.
              </p>
            </ScrollReveal>
            <ScrollReveal delay={100} className="bg-white rounded-2xl p-6 border-2 border-primary/20">
              <div className="flex items-center gap-2 mb-2">
                <Droplet className="w-5 h-5 text-sky" />
                <h3 className="font-display font-semibold text-ink">En parler autour de vous</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Le geste qui inspire un autre geste : partagez Helios à un proche qui hésite encore
                à se lancer. Aucune contrepartie à en attendre — juste un service de plus rendu.
              </p>
            </ScrollReveal>
          </div>
        </div>
      </section>

      <CtaFaisTaPart />
    </>
  )
}
