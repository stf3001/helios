/**
 * « Le vent » — la page chapeau de l'éolien domestique.
 *
 * PAS DE SIMULATEUR ICI. Le chiffrage vit dans « La maison de demain », où l'éolienne se
 * pose à côté des panneaux, du stockage et du reste — c'est là qu'on voit ce qu'elle
 * change vraiment. Cette page explique, et renvoie.
 *
 * Le contenu vient du projet EOLIA : caractéristiques de la Tulipe, chaîne de conversion,
 * prêt d'anémomètre, démarches d'urbanisme, tenue au vent fort. Repris de leurs pages
 * plutôt que réécrit de mémoire.
 */

import { Link } from 'react-router-dom'
import {
  ArrowRight, Compass, Gauge, Layers, Leaf, Ruler, ShieldCheck, Volume2, Wrench,
} from 'lucide-react'

import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useTitle } from '../hooks/useTitle'

/** Ce qui distingue une éolienne verticale d'une éolienne à hélice. */
const ATOUTS = [
  { icon: Compass, titre: 'Elle prend le vent de partout',
    texte: 'Pas de girouette, pas de moteur d’orientation : les pales hélicoïdales captent le vent quelle que soit sa direction. C’est ce qui la rend utile en ville et entre des bâtiments, là où le vent tourne sans arrêt.' },
  { icon: Volume2, titre: 'Moins de 35 dB à cinq mètres',
    texte: 'Moins qu’un réfrigérateur. C’est la première question que posent les voisins, et la réponse est rassurante.' },
  { icon: ShieldCheck, titre: 'Sans pales tranchantes',
    texte: 'La forme fermée du rotor ne présente pas de bout de pale à grande vitesse : pas de danger pour les oiseaux, ni pour ce qui passe à côté.' },
  { icon: Gauge, titre: 'Elle démarre dès 2 m/s',
    texte: 'Une brise suffit à la lancer. Elle est conçue pour les vents turbulents, ceux que les éoliennes à hélice n’exploitent pas.' },
  { icon: Wrench, titre: 'Presque rien à entretenir',
    texte: 'Un contrôle visuel par an — pales, fixations, câbles. Aucune lubrification, les roulements sont étanches. Comptez trente minutes.' },
  { icon: Leaf, titre: 'Matériaux recyclables',
    texte: 'Peu de pièces mobiles, une conception robuste, et une durée de vie annoncée d’au moins vingt-cinq ans.' },
]

/** La chaîne de conversion, du vent à la prise. */
const ETAPES = [
  { titre: 'Le vent fait tourner le rotor',
    texte: 'Les pales hélicoïdales captent l’énergie du vent, d’où qu’il vienne. Leur forme donne le couple nécessaire au démarrage.' },
  { titre: 'La rotation devient du courant',
    texte: 'Un alternateur à aimants permanents convertit le mouvement en électricité.' },
  { titre: 'L’onduleur le rend utilisable',
    texte: 'Il transforme le courant en 230 V compatible avec votre installation, et pilote le stockage s’il y en a un.' },
  { titre: 'Vous consommez, puis vous stockez',
    texte: 'L’électricité alimente la maison en priorité. Le surplus part en batterie, ou au réseau.' },
]

/** Ce qu'il faut avoir en tête avant de signer. */
const AVANT = [
  { icon: Ruler, titre: 'Sous 1,80 m, aucune démarche d’urbanisme',
    texte: 'Du sol au sommet de la machine. La production est un peu plus basse qu’avec un mât, mais on évite la déclaration préalable : une simple notice et une déclaration à Enedis suffisent. Au-delà, comptez une déclaration préalable, et un permis de construire à partir de 12 mètres.' },
  { icon: Layers, titre: 'Plusieurs éoliennes valent mieux qu’une',
    texte: 'Placées côte à côte, elles s’accélèrent mutuellement le vent — c’est l’effet Venturi, le même qui fait souffler plus fort entre deux immeubles. Le constructeur compte +5 % de production dès la deuxième machine, et propose des supports pour les monter en grappe, jusqu’à six.' },
  { icon: ShieldCheck, titre: 'La tempête est prévue',
    texte: 'Un freinage automatique ralentit puis arrête les pales au-delà de 25 m/s, soit 90 km/h. À l’arrêt, la machine est conçue pour tenir des vents de 180 km/h.' },
  { icon: Gauge, titre: 'Ce qu’on peut en attendre',
    texte: 'Une éolienne de 3 kW produit entre 3 000 et 6 000 kWh par an selon l’exposition. L’écart entre ces deux chiffres, c’est exactement ce que l’anémomètre sert à trancher — et de toute façon, c’est la mesure qui fait foi, pas l’estimation.' },
]

export default function Vent() {
  useTitle('Le vent — l’éolien domestique | HELIOS')
  return (
    <>
      <Hero
        title="Le vent, quand le soleil se couche"
        subtitle="Il souffle la nuit et en hiver, précisément quand les panneaux ne donnent plus rien. Une éolienne ne remplace pas le solaire : elle le complète, et les deux ensemble couvrent l’année."
      />

      <section className="mx-auto max-w-[1100px] px-4 py-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Pourquoi une éolienne verticale
        </h2>
        <p className="mt-3 max-w-[760px] text-lg text-dark/80">
          L’éolienne à hélice qu’on voit dans les champs a besoin d’un vent régulier et
          d’un mât haut. Chez un particulier, le vent est turbulent : il rebondit sur les
          toits, les arbres, les murs, et change sans arrêt de direction. Une verticale est
          faite pour ça.
        </p>
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {ATOUTS.map((a) => (
            <div key={a.titre} className="rounded-2xl border border-ink/10 bg-white p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky/10">
                <a.icon className="h-5 w-5 text-sky" />
              </div>
              <h3 className="mt-3 font-display text-lg font-bold text-ink">{a.titre}</h3>
              <p className="mt-1.5 text-dark/75">{a.texte}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-cream py-12">
        <div className="mx-auto max-w-[1100px] px-4">
          <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
            Du vent à la prise, en quatre temps
          </h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {ETAPES.map((e, i) => (
              <div key={e.titre} className="rounded-2xl border border-ink/10 bg-white p-5">
                <span className="font-display text-2xl font-bold text-primary">{i + 1}</span>
                <h3 className="mt-1 font-display text-lg font-bold text-ink">{e.titre}</h3>
                <p className="mt-1.5 text-dark/75">{e.texte}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* L'anémomètre : ce que personne d'autre ne propose, donc ce qu'il faut raconter. */}
      <section className="mx-auto max-w-[1100px] px-4 py-12">
        <div className="rounded-2xl border-2 border-primary bg-white p-6 sm:p-8">
          <h2 className="font-display text-2xl font-bold text-ink">
            On vous prête un anémomètre. Gratuitement.
          </h2>
          <p className="mt-3 max-w-[760px] text-lg text-dark/80">
            C’est le point qui change tout. Les données météo régionales donnent une
            estimation ; votre terrain, lui, est unique. La topographie, les bâtiments
            autour, les arbres : tout cela pèse plus lourd sur le vent que la moyenne du
            département.
          </p>
          <ol className="mt-6 space-y-3">
            {[
              ['Vous recevez l’appareil', 'Un anémomètre professionnel, prêté un mois, contre une caution. Bon de retour prépayé inclus.'],
              ['Vous le plantez à l’endroit prévu', 'Un mois suffit à obtenir des données représentatives de votre site.'],
              ['Vous renvoyez les relevés', 'Avec le bon prépayé, et vous récupérez votre caution.'],
              ['L’estimation est recalée sur VOTRE terrain', 'Ce ne sont plus des moyennes régionales : ce sont vos chiffres.'],
            ].map(([titre, texte], i) => (
              <li key={titre} className="flex items-start gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full
                  bg-primary text-sm font-bold text-white">{i + 1}</span>
                <span className="text-dark/80">
                  <strong className="text-ink">{titre}</strong> — {texte}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mx-auto max-w-[1100px] px-4 pb-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Ce qu’il faut savoir avant de se décider
        </h2>
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          {AVANT.map((b) => (
            <div key={b.titre} className="rounded-2xl border border-ink/10 bg-white p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <b.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-3 font-display text-lg font-bold text-ink">{b.titre}</h3>
              <p className="mt-1.5 text-dark/75">{b.texte}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pas de simulateur ici : il vit dans « La maison de demain », et c'est voulu. */}
      <section className="mx-auto max-w-[1100px] px-4 pb-12">
        <div className="rounded-2xl bg-ink p-6 text-white sm:p-8">
          <h2 className="font-display text-2xl font-bold">
            Combien chez vous ? Le simulateur le dit.
          </h2>
          <p className="mt-2 max-w-[700px] text-white/85">
            L’éolienne n’a pas de page de calcul à elle : elle se pose dans « La maison de
            demain », à côté des panneaux, du stockage et de la voiture. C’est là qu’on voit
            ce qu’elle change — parce que la bonne question n’est pas « combien produit une
            éolienne », mais « combien elle me fait économiser, en plus du reste ».
          </p>
          <Link to="/simulateur-solaire"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3
              font-semibold text-ink transition hover:bg-cream">
            Équiper ma maison <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-[1100px] px-4 pb-16">
        <FichesLiees cats={['eolien']} titre="Vos questions sur l’éolien" />
      </section>
    </>
  )
}
