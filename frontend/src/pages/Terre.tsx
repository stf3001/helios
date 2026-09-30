/**
 * « La terre » — la page chapeau du jardin nourricier.
 *
 * PAS DE CALCULATEUR ICI, comme sur « Le vent » et « L'eau ». Le chiffrage vit dans
 * « La maison de demain », sur le potager de la scène : deux calculateurs qui disent la
 * même chose finissent toujours par ne plus la dire pareil. Cette page explique, et
 * renvoie.
 *
 * CE QUI FAIT QUE CETTE PAGE APPARTIENT À HELIOS et pas à un blog de jardinage :
 * l'hydroponie consomme de l'électricité. C'est le même raisonnement que sur l'eau
 * atmosphérique — un surplus solaire qui partait au réseau pour un centime devient
 * quelque chose d'utile. Sans ce fil, la terre serait hors sujet sur un site d'énergie.
 *
 * Le contenu éditorial (intro, sections) vit dans `data/piliers.json`, source unique
 * partagée avec le pré-rendu SEO : la version servie aux moteurs dit donc exactement la
 * même chose que la page. Ici ne vit que ce que le gabarit générique ne sait pas faire.
 */

import { Link } from 'react-router-dom'
import {
  ArrowRight, CalendarDays, Clock, Home, Lightbulb, MessageSquare, Sprout, Sun,
} from 'lucide-react'

import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useTitle } from '../hooks/useTitle'
import piliers from '../data/piliers.json'

const PILIER = piliers.find((p) => p.slug === 'la-terre')!

/** Les trois façons de cultiver, et ce que chacune tient vraiment. */
const FACONS = [
  {
    icon: Sprout,
    titre: 'Dehors, en pleine terre',
    texte:
      'C’est là que se fait le volume. Une planche de légumes bien tenue donne 2 à 3 kg '
      + 'par m² et par an ; un jardin débutant, plutôt 1,5. Le sol, l’exposition et la '
      + 'régularité comptent plus que le matériel.',
    tenir: 'Le gros des légumes',
  },
  {
    icon: Home,
    titre: 'Dedans, sur un rebord',
    texte:
      'Aromatiques, jeunes pousses, radis : ça marche, et c’est immédiat. Tomates et '
      + 'courgettes, non — elles réclament une lumière qu’un vitrage ne donne pas, quoi '
      + 'qu’en disent les catalogues.',
    tenir: 'Le goût, pas le volume',
  },
  {
    icon: Lightbulb,
    titre: 'Hors-sol, sous lampes',
    texte:
      'Croissance rapide, récolte régulière, indépendante des saisons. Mais l’éclairage '
      + 'tourne douze à seize heures par jour : c’est cette consommation, et elle seule, '
      + 'qui décide si l’opération a du sens.',
    tenir: 'Du frais toute l’année, contre des kWh',
  },
]

export default function Terre() {
  useTitle('La terre — cultiver ses légumes chez soi | HELIOS')
  return (
    <>
      <Hero title="La terre, et ce qu’elle rend vraiment" subtitle={PILIER.sousTitre} />

      <section className="mx-auto max-w-[900px] px-4 py-12">
        <p className="text-lg text-dark/80">{PILIER.intro}</p>
      </section>

      {/* Le conseil qui compte plus que tous les autres, donc mis en avant et seul. */}
      <section className="mx-auto max-w-[900px] px-4 pb-12">
        <div className="rounded-2xl border-2 border-primary bg-white p-6 sm:p-8">
          <div className="flex items-center gap-2">
            <Clock className="h-6 w-6 shrink-0 text-primary" />
            <h2 className="font-display text-2xl font-bold text-ink">
              Commencez par le temps, pas par la surface
            </h2>
          </div>
          <p className="mt-3 text-lg text-dark/80">
            {PILIER.sections[0].contenu}
          </p>
          <p className="mt-4 rounded-xl bg-cream p-4 text-dark/80">
            <strong className="text-ink">Et le travail n’est pas régulier.</strong>{' '}
            {PILIER.sections[1].contenu}
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-[1100px] px-4 pb-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Trois façons de cultiver, trois résultats différents
        </h2>
        <div className="mt-6 grid gap-5 md:grid-cols-3">
          {FACONS.map((f) => (
            <div key={f.titre} className="rounded-2xl border border-ink/10 bg-white p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-leaf/10">
                <f.icon className="h-5 w-5 text-leaf" />
              </div>
              <h3 className="mt-3 font-display text-lg font-bold text-ink">{f.titre}</h3>
              <p className="mt-1.5 text-dark/75">{f.texte}</p>
              <p className="mt-3 text-sm font-semibold text-primary">{f.tenir}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Le parler-vrai, au même endroit et dans la même forme que sur « L'eau ». */}
      <section className="mx-auto max-w-[900px] px-4 pb-12">
        <div className="rounded-r-2xl border-l-4 border-primary bg-gray-50 p-6 text-gray-700">
          <strong>Le parler-vrai d’Helios.</strong> Un potager ne rend pas un foyer
          autonome, et personne ne devrait vous le vendre ainsi. Couvrir les légumes
          d’une famille de quatre toute l’année demande de l’ordre de 300 à 500 m² et
          plus de deux heures par jour en moyenne — c’est un métier, pas un loisir de
          week-end. Ce qui est parfaitement atteignable, en revanche, c’est une bonne
          part de vos légumes sur une heure par jour. C’est ce que notre calculateur
          vous montre, et il ne rogne aucun chiffre pour vous faire plaisir.
        </div>
      </section>

      {/* L'hydroponie : le fil qui relie cette page au reste du site. */}
      <section className="mx-auto max-w-[900px] px-4 pb-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          {PILIER.sections[3].titre}
        </h2>
        <p className="mt-3 text-lg text-dark/80">{PILIER.sections[3].contenu}</p>
        <div className="mt-4 flex items-start gap-2 text-dark/75">
          <Sun className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
          <span>
            C’est le même raisonnement que pour{' '}
            <Link to="/eau" className="text-primary underline">l’eau atmosphérique</Link> :
            une consommation qui n’a de sens que si vous produisez déjà votre électricité.
          </span>
        </div>
      </section>

      {/* Le chiffrage, qui vit dans la scène — et le programme, qui vit dans l'espace. */}
      <section className="mx-auto max-w-[900px] px-4 pb-12">
        <div className="rounded-2xl border border-leaf/20 bg-leaf/5 p-8 text-center">
          <Sprout className="mx-auto mb-3 h-10 w-10 text-leaf" />
          <h2 className="font-display text-2xl font-bold text-ink">
            Combien de légumes chez vous ?
          </h2>
          <p className="mx-auto mt-2 max-w-[560px] text-dark/75">
            Dites votre foyer et le temps que vous acceptez d’y passer : le calculateur
            répond en mètres carrés, en kilos et en part de vos légumes. Il vit sur le
            potager de « la maison de demain », à côté des panneaux et du reste — parce
            que tout se tient.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link to="/simulateur-solaire"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3
                font-semibold text-white transition-colors hover:bg-terra">
              Calculer mon potager <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/helios"
              className="inline-flex items-center gap-2 rounded-xl border border-ink/25 px-6 py-3
                font-semibold text-ink transition-colors hover:border-ink hover:bg-ink hover:text-sable">
              <MessageSquare className="h-4 w-4" /> Poser mes questions à Helios
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[900px] px-4 pb-12">
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl
          border border-ink/10 bg-white p-6">
          <div className="flex items-start gap-3">
            <CalendarDays className="mt-0.5 h-6 w-6 shrink-0 text-primary" />
            <div>
              <h2 className="font-display text-lg font-bold text-ink">
                Votre programme de cultures, mois par mois
              </h2>
              <p className="mt-1 text-dark/75">
                Quoi semer, quoi repiquer, quoi récolter — adapté à votre moitié de la
                France. Gratuit, dans votre espace.
              </p>
            </div>
          </div>
          <Link to="/espace/jardin"
            className="shrink-0 rounded-xl bg-primary px-5 py-2.5 font-semibold text-white
              hover:opacity-90">
            Voir mon programme
          </Link>
        </div>
      </section>

      {/* Sans enveloppe : `FichesLiees` apporte sa propre `<section>` et son rembourrage,
          et s'efface entièrement quand aucune fiche ne correspond. L'envelopper laisserait
          un blanc en bas de page le jour où la catégorie serait vide. */}
      <FichesLiees cats={['jardin']} titre="Vos questions sur le potager" />
    </>
  )
}
