/**
 * « La terre » — la page chapeau de ce que le sol donne : des légumes, et de la température.
 *
 * DEUX SUJETS, UN SEUL SOL, ET ILS N'ONT RIEN À VOIR. Le potager et le puits canadien ne se
 * lisent pas l'un après l'autre : on vient pour l'un ou pour l'autre. D'où le sous-menu en
 * haut, et non deux moitiés empilées — la page ferait le double de haut et chacun ferait
 * défiler la moitié qui ne l'intéresse pas.
 *
 * PAS DE CALCULATEUR ICI, comme sur « Le vent » et « L'eau ». Le chiffrage du potager vit
 * dans « La maison de demain », sur le potager de la scène : deux calculateurs qui disent la
 * même chose finissent toujours par ne plus la dire pareil. Cette page explique, et renvoie.
 *
 * CE QUI FAIT QUE CETTE PAGE APPARTIENT À HELIOS et pas à un blog de jardinage : l'hydroponie
 * consomme de l'électricité, et le puits canadien en fait économiser. C'est le même
 * raisonnement que sur l'eau atmosphérique. Sans ce fil, la terre serait hors sujet sur un
 * site d'énergie.
 *
 * LE PUITS CANADIEN N'EST PAS CHIFFRÉ, ET C'EST VOULU (demande de Stéphane, 01/10/2026) : ce
 * qu'il fait gagner dépend du climat, du sol, de la ventilation et de ce qu'on chauffe. Un
 * calculateur viendra ; d'ici là, aucun euro n'est avancé. Voir `TODO.md`.
 *
 * Le contenu éditorial (intro, sections) vit dans `data/piliers.json`, source unique partagée
 * avec le pré-rendu SEO : la version servie aux moteurs dit donc exactement la même chose que
 * la page. Ici ne vit que ce que le gabarit générique ne sait pas faire.
 */

import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  ArrowRight, CalendarDays, Clock, Flame, Home, Lightbulb, MessageSquare, Shovel,
  Snowflake, Sprout, Sun, Thermometer, type LucideIcon,
} from 'lucide-react'

import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useTitle } from '../hooks/useTitle'
import piliers from '../data/piliers.json'

const PILIER = piliers.find((p) => p.slug === 'la-terre')!

type Sujet = 'potager' | 'puits-canadien'

const SUJETS: { id: Sujet; label: string; Icone: LucideIcon; phrase: string }[] = [
  {
    id: 'potager',
    label: 'Le potager',
    Icone: Sprout,
    phrase: 'Ce qu’une heure par jour rend vraiment, en mètres carrés et en kilos.',
  },
  {
    id: 'puits-canadien',
    label: 'Le puits canadien',
    Icone: Thermometer,
    phrase: 'La fraîcheur de l’été et la douceur de l’hiver, prises à deux mètres sous la pelouse.',
  },
]

/** Les trois façons de cultiver, et ce que chacune tient vraiment. */
const FACONS = [
  {
    icon: Sprout,
    titre: 'Dehors, en pleine terre',
    texte:
      'C’est là que se fait le volume : 2 à 3 kg par m² et par an pour une planche bien '
      + 'tenue, plutôt 1,5 quand on débute. Le sol et la régularité comptent plus que le '
      + 'matériel.',
    tenir: 'Le gros des légumes',
  },
  {
    icon: Home,
    titre: 'Dedans, sur un rebord',
    texte:
      'Aromatiques, jeunes pousses, radis : immédiat, et ça marche. Tomates et courgettes, '
      + 'non — elles réclament une lumière qu’un vitrage ne donne pas.',
    tenir: 'Le goût, pas le volume',
  },
  {
    icon: Lightbulb,
    titre: 'Hors-sol, sous lampes',
    texte:
      'Récolte régulière, indépendante des saisons. Mais l’éclairage tourne douze à seize '
      + 'heures par jour : c’est cette consommation, et elle seule, qui décide.',
    tenir: 'Du frais toute l’année, contre des kWh',
  },
]

/** Les deux saisons du puits canadien, chacune avec sa section éditoriale. */
const SAISONS = [
  { icon: Snowflake, couleur: 'text-sky', fond: 'bg-sky/10', section: 5 },
  { icon: Flame, couleur: 'text-terra', fond: 'bg-terra/10', section: 6 },
]

/* ------------------------------------------------------------------- Potager */

function Potager() {
  return (
    <>
      {/* Le conseil qui compte plus que tous les autres, donc mis en avant et seul. */}
      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-2xl border-2 border-primary bg-white p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 shrink-0 text-primary" />
            <h2 className="font-display text-xl font-bold text-ink">
              Commencez par le temps, pas par la surface
            </h2>
          </div>
          <p className="mt-2 text-dark/80">{PILIER.sections[0].contenu}</p>
          <p className="mt-3 rounded-xl bg-cream p-3 text-sm text-dark/80">
            <strong className="text-ink">Et le travail n’est pas régulier.</strong>{' '}
            {PILIER.sections[1].contenu}
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-[1100px] px-4 pb-8">
        <h2 className="font-display text-xl font-bold text-ink md:text-2xl">
          Trois façons de cultiver, trois résultats différents
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {FACONS.map((f) => (
            <div key={f.titre} className="rounded-2xl border border-ink/10 bg-white p-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-leaf/10">
                <f.icon className="h-5 w-5 text-leaf" />
              </div>
              <h3 className="mt-2 font-display text-lg font-bold text-ink">{f.titre}</h3>
              <p className="mt-1 text-sm text-dark/75">{f.texte}</p>
              <p className="mt-2 text-sm font-semibold text-primary">{f.tenir}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Le parler-vrai, au même endroit et dans la même forme que sur « L'eau ». */}
      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-r-2xl border-l-4 border-primary bg-gray-50 p-5 text-gray-700">
          <strong>Le parler-vrai d’Helios.</strong> Un potager ne rend pas un foyer autonome,
          et personne ne devrait vous le vendre ainsi. Couvrir les légumes d’une famille de
          quatre toute l’année demande de l’ordre de 300 à 500 m² et plus de deux heures par
          jour — c’est un métier, pas un loisir de week-end. Ce qui est parfaitement
          atteignable, en revanche, c’est une bonne part de vos légumes sur une heure par
          jour. C’est ce que notre calculateur montre, et il ne rogne aucun chiffre pour vous
          faire plaisir.
        </div>
      </section>

      {/* L'hydroponie : le fil qui relie le potager au reste du site. */}
      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <h2 className="font-display text-xl font-bold text-ink md:text-2xl">
          {PILIER.sections[3].titre}
        </h2>
        <p className="mt-2 text-dark/80">{PILIER.sections[3].contenu}</p>
        <p className="mt-3 flex items-start gap-2 text-sm text-dark/75">
          <Sun className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <span>
            C’est le même raisonnement que pour{' '}
            <Link to="/eau" className="text-primary underline">l’eau atmosphérique</Link> :
            une consommation qui n’a de sens que si vous produisez déjà votre électricité.
          </span>
        </p>
      </section>

      {/* Le chiffrage, qui vit dans la scène — et le programme, qui vit dans l'espace. */}
      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-2xl border border-leaf/20 bg-leaf/5 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Sprout className="mt-0.5 h-7 w-7 shrink-0 text-leaf" />
              <div>
                <h2 className="font-display text-xl font-bold text-ink">
                  Combien de légumes chez vous ?
                </h2>
                <p className="mt-1 max-w-[560px] text-sm text-dark/75">
                  Dites votre foyer et le temps que vous acceptez d’y passer : le calculateur
                  répond en mètres carrés, en kilos et en part de vos légumes. Il vit sur le
                  potager de « la maison de demain », à côté des panneaux — parce que tout se
                  tient.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link to="/simulateur-solaire"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5
                  font-semibold text-white transition-colors hover:bg-terra">
                Calculer mon potager <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/helios"
                className="inline-flex items-center gap-2 rounded-xl border border-ink/25 px-5
                  py-2.5 font-semibold text-ink transition-colors hover:border-ink
                  hover:bg-ink hover:text-sable">
                <MessageSquare className="h-4 w-4" /> Mes questions
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl
          border border-ink/10 bg-white p-5">
          <div className="flex items-start gap-3">
            <CalendarDays className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
            <div>
              <h2 className="font-display text-lg font-bold text-ink">
                Votre programme de cultures, mois par mois
              </h2>
              <p className="mt-0.5 text-sm text-dark/75">
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

/* ------------------------------------------------------- Puits canadien */

function PuitsCanadien() {
  /* Le schéma est fourni à part. Tant que le fichier n'est pas déposé, la figure s'efface
     d'elle-même plutôt que d'afficher une image cassée — la page reste juste, avant comme
     après. Déposer l'image dans `frontend/public/` sous ce nom suffit à la faire paraître. */
  const [schema, setSchema] = useState(true)

  return (
    <>
      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-2xl border-2 border-primary bg-white p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <Thermometer className="h-5 w-5 shrink-0 text-primary" />
            <h2 className="font-display text-xl font-bold text-ink">
              {PILIER.sections[4].titre}
            </h2>
          </div>
          <p className="mt-2 text-dark/80">{PILIER.sections[4].contenu}</p>
        </div>
      </section>

      {schema && (
        <section className="mx-auto max-w-[900px] px-4 pb-8">
          <figure className="overflow-hidden rounded-2xl border border-ink/10 bg-white">
            <img
              src="/schema-puits-canadien.webp"
              alt="L’air extérieur entre par une prise d’air filtrée, parcourt un tuyau enterré à deux mètres où il prend la température du sol, puis rejoint la ventilation de la maison."
              className="w-full"
              loading="lazy"
              onError={() => setSchema(false)}
            />
          </figure>
        </section>
      )}

      <section className="mx-auto max-w-[1100px] px-4 pb-8">
        <div className="grid gap-4 md:grid-cols-2">
          {SAISONS.map(({ icon: Icone, couleur, fond, section }) => (
            <div key={section} className="rounded-2xl border border-ink/10 bg-white p-5">
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${fond}`}>
                <Icone className={`h-5 w-5 ${couleur}`} />
              </div>
              <h2 className="mt-2 font-display text-lg font-bold text-ink">
                {PILIER.sections[section].titre}
              </h2>
              <p className="mt-1 text-sm text-dark/75">{PILIER.sections[section].contenu}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Le parler-vrai, dans la même forme que sur le potager et sur « L'eau ». */}
      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-r-2xl border-l-4 border-primary bg-gray-50 p-5 text-gray-700">
          <strong>Le parler-vrai d’Helios.</strong> Un puits canadien ne climatise pas et ne
          chauffe pas : il tempère l’air neuf avant qu’il n’entre, et c’est tout. Si votre
          maison est mal isolée ou surchauffée par ses vitrages, il n’y changera presque rien
          — l’isolation passe avant, comme toujours. Et il ne vaut que ce que vaut sa pose :
          mal dimensionné ou mal incliné, il ne fait rien du tout.
        </div>
      </section>

      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-2xl border border-ink/10 bg-white p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <Shovel className="h-5 w-5 shrink-0 text-primary" />
            <h2 className="font-display text-xl font-bold text-ink">
              {PILIER.sections[7].titre}
            </h2>
          </div>
          <p className="mt-2 text-dark/80">{PILIER.sections[7].contenu}</p>
        </div>
      </section>

      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-2xl border border-leaf/20 bg-leaf/5 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Thermometer className="mt-0.5 h-7 w-7 shrink-0 text-leaf" />
              <div>
                <h2 className="font-display text-xl font-bold text-ink">
                  Voir où il se place dans la maison
                </h2>
                <p className="mt-1 max-w-[560px] text-sm text-dark/75">
                  Le puits canadien est posé dans « la maison de demain », à côté des
                  panneaux, de la batterie et du reste. Vous verrez où il arrive, et ce
                  qu’il côtoie.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link to="/simulateur-solaire"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5
                  font-semibold text-white transition-colors hover:bg-terra">
                La maison de demain <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/helios"
                className="inline-flex items-center gap-2 rounded-xl border border-ink/25 px-5
                  py-2.5 font-semibold text-ink transition-colors hover:border-ink
                  hover:bg-ink hover:text-sable">
                <MessageSquare className="h-4 w-4" /> Mes questions
              </Link>
            </div>
          </div>
        </div>
      </section>

      <FichesLiees cats={['puits_canadien']} titre="Vos questions sur le puits canadien" />
    </>
  )
}

/* ------------------------------------------------------------------ La page */

export default function Terre() {
  useTitle('La terre — potager et puits canadien | HELIOS')

  /* Le sujet vit dans l'URL : un lien peut viser directement le puits canadien, et un
     retour en arrière ramène là où on était. `replace` pour ne pas empiler une entrée
     d'historique à chaque aller-retour entre les deux boutons. */
  const [params, setParams] = useSearchParams()
  const sujet: Sujet = params.get('sujet') === 'puits-canadien' ? 'puits-canadien' : 'potager'
  const actif = SUJETS.find((s) => s.id === sujet)!

  return (
    <>
      <Hero title="La terre, et ce qu’elle rend vraiment" subtitle={PILIER.sousTitre} />

      {/* Le bandeau : la phrase qui tient les deux sujets ensemble, puis le choix. */}
      <section className="mx-auto max-w-[900px] px-4 pb-6 pt-8">
        <p className="text-lg text-dark/80">{PILIER.intro}</p>

        <div role="tablist" aria-label="Les deux sujets de la terre"
          className="mt-5 flex flex-wrap gap-2">
          {SUJETS.map(({ id, label, Icone }) => (
            <button key={id} role="tab" type="button" aria-selected={sujet === id}
              onClick={() => setParams(id === 'potager' ? {} : { sujet: id }, { replace: true })}
              className={`inline-flex items-center gap-2 rounded-xl border px-5 py-2.5
                font-semibold transition-colors
                ${sujet === id
                  ? 'border-primary bg-primary text-white'
                  : 'border-ink/20 text-ink hover:border-ink hover:bg-white'}`}>
              <Icone className="h-4 w-4" aria-hidden="true" /> {label}
            </button>
          ))}
        </div>

        <p className="mt-3 text-dark/70">{actif.phrase}</p>
      </section>

      {sujet === 'potager' ? <Potager /> : <PuitsCanadien />}
    </>
  )
}
