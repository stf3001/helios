import { Link } from 'react-router-dom'
import { Droplets, Wind, Snowflake, Filter, BadgeCheck, Users, Building2, Landmark, Sun, MessageSquare } from 'lucide-react'
import Hero from '../components/Hero'
import { useTitle } from '../hooks/useTitle'

// Section publique « L'eau » — deuxième pilier de la maison autonome après l'énergie.
// Contenu strictement public/pédagogique (mêmes règles que kb/eau.md).

const ETAPES = [
  { icon: Wind, titre: 'Captation', texte: "L'appareil aspire l'air ambiant et capte son humidité." },
  { icon: Snowflake, titre: 'Condensation', texte: "L'humidité est condensée en eau, comme la rosée du matin." },
  { icon: Filter, titre: 'Filtration', texte: "L'eau est filtrée et purifiée en plusieurs étapes." },
  { icon: BadgeCheck, titre: 'Contrôle chez vous', texte: 'Un kit d\'analyse permet de vérifier la potabilité sur place.' },
]

const PUBLICS = [
  {
    icon: Users, titre: 'Familles',
    texte: 'Une eau de boisson maîtrisée, sans bouteilles plastiques à acheter, transporter et jeter.',
  },
  {
    icon: Landmark, titre: 'Collectivités',
    texte: 'Autonomie hydrique pour écoles, mairies et équipements publics — chaque litre produit soulage le réseau.',
  },
  {
    icon: Building2, titre: 'Entreprises',
    texte: 'Bureaux, hôtels, restaurants : une eau de qualité pour vos clients et collaborateurs.',
  },
]

export default function Eau() {
  useTitle("L'eau — produire son eau chez soi")
  return (
    <>
      <Hero
        title="De l'eau, extraite de l'air."
        subtitle="Après l'énergie, l'eau : la maison de demain peut aussi produire son eau de boisson. Helios vous explique, chiffre, et vous dit franchement si c'est pertinent chez vous."
      />

      {/* Comment ça marche */}
      <section className="max-w-[900px] mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold mb-2">Comment ça marche ?</h2>
        <p className="text-gray-600 mb-8">
          Un générateur d'eau atmosphérique (AWG) transforme l'humidité de l'air en eau potable.
          Plus l'air est chaud et humide, plus il produit.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ETAPES.map((e, i) => (
            <div key={e.titre} className="border border-gray-200 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <e.icon className="w-6 h-6 text-sky" />
                <span className="text-xs text-gray-400 font-semibold">{i + 1}</span>
              </div>
              <div className="font-semibold">{e.titre}</div>
              <div className="text-sm text-gray-600 mt-1">{e.texte}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Le parler-vrai Helios */}
      <section className="max-w-[900px] mx-auto px-4 pb-12">
        <div className="border-l-4 border-primary bg-gray-50 rounded-r-2xl p-6 text-gray-700">
          <strong>Le parler-vrai d'Helios.</strong> L'eau atmosphérique ne remplace pas l'eau du robinet —
          pour la douche ou le lave-linge, le réseau reste imbattable. Elle se positionne sur l'eau de
          boisson et de cuisine, face à l'eau en bouteille (déchets plastiques, transport, microplastiques),
          et comme solution d'autonomie pour les sites isolés. Et comme elle consomme de l'électricité,
          elle prend tout son sens couplée à une production solaire : votre surplus devient de l'eau potable.
        </div>
      </section>

      {/* Pour qui */}
      <section className="max-w-[900px] mx-auto px-4 pb-12">
        <h2 className="text-2xl font-bold mb-6">Pour qui ?</h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {PUBLICS.map((p) => (
            <div key={p.titre} className="border border-gray-200 rounded-2xl p-5">
              <p.icon className="w-6 h-6 text-sky mb-2" />
              <div className="font-semibold">{p.titre}</div>
              <div className="text-sm text-gray-600 mt-1">{p.texte}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Simulateur — le cœur de la section */}
      <section className="max-w-[900px] mx-auto px-4 pb-12">
        <div className="bg-sky/5 border border-sky/20 rounded-2xl p-8 text-center">
          <Droplets className="w-10 h-10 text-sky mx-auto mb-3" />
          <h2 className="text-2xl font-bold mb-2">Combien d'eau chez vous ?</h2>
          <p className="text-gray-600 max-w-[560px] mx-auto mb-6">
            La production dépend du climat de votre région, mois par mois. Notre simulateur croise les
            tables de production réelles avec la météo de votre ville — en fourchettes, jamais en promesses.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/potentiel-hydrique"
              className="rounded-xl bg-sky text-white font-semibold px-6 py-3 hover:opacity-90">
              Estimer mon potentiel hydrique
            </Link>
            <Link to="/helios"
              className="inline-flex items-center gap-2 rounded-xl border border-sky text-sky font-semibold px-6 py-3 hover:bg-sky/5">
              <MessageSquare className="w-4 h-4" /> Poser mes questions à Helios
            </Link>
          </div>
        </div>
      </section>

      {/* Partenaire — transparence */}
      <section className="max-w-[900px] mx-auto px-4 pb-16">
        <h2 className="text-2xl font-bold mb-4">Notre partenaire : Hydrolia</h2>
        <p className="text-gray-700 mb-4">
          Hydrolia est née autour d'une table, entre amis — des parents, professionnels de l'ingénierie,
          de la santé et de l'environnement, réunis par l'envie de faire leur part. Leur signature :
          « de l'eau pure, extraite de l'air », avec une exigence rare de transparence — chaque appareil
          est livré avec un kit permettant de <strong>vérifier la potabilité chez vous</strong>, pas sur une brochure,
          et une application connectée suit la production et l'entretien des filtres.
        </p>
        <p className="text-sm text-gray-600 mb-6">
          Ordre de grandeur : modèle familial 20 L/jour autour de 1 990 € TTC, kit de certification inclus —
          à confirmer au devis. Gamme jusqu'aux besoins collectifs.
        </p>
        <div className="border-l-4 border-primary bg-gray-50 rounded-r-2xl p-5 text-sm text-gray-700 mb-8">
          <strong>Transparence.</strong> HELIOS est apporteur d'affaires d'Hydrolia : si vous équipez votre
          maison via nous, Hydrolia nous verse une commission — jamais vous. Notre avis reste indépendant,
          et nous vous dirons franchement si la solution n'est pas pertinente chez vous.
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Sun className="w-4 h-4 text-primary shrink-0" />
          <span>
            L'eau atmosphérique est encore meilleure couplée au solaire —{' '}
            <Link to="/simulateur-solaire" className="text-primary underline">estimez aussi votre potentiel solaire</Link>.
          </span>
        </div>
      </section>
    </>
  )
}
