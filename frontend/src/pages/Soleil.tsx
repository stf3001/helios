/**
 * « Le soleil » — la page chapeau du photovoltaïque.
 *
 * ELLE MANQUAIT AU MENU (constat de Stéphane, 05/10/2026) : le vent, l'eau, la terre et
 * l'achat d'énergie avaient leur page, le soleil n'avait que la page chapeau générique
 * tirée de `piliers.json` — le sujet le plus demandé du site était le moins raconté.
 *
 * ELLE REPREND L'ADRESSE `/solaire`, elle n'en crée pas une nouvelle. C'était le point à
 * trancher : `/solaire` existe depuis la campagne de référencement, elle est dans le plan
 * de site, et quarante-cinq fiches de la FAQ pointent dessus (« Sujet : Le solaire »).
 * Ouvrir `/le-soleil` à côté aurait fabriqué deux pages sur le même sujet — ce que les
 * moteurs sanctionnent, et ce qui aurait coupé la page de tous ses liens entrants.
 * `/le-soleil` existe quand même, mais en simple redirection (voir `App.tsx`), par
 * symétrie avec `/le-vent` et `/la-terre`.
 *
 * PAS DE SIMULATEUR ICI, comme sur « Le vent », « L'eau » et « La terre » : le chiffrage
 * vit dans « La maison de demain », et deux calculateurs qui disent la même chose finissent
 * toujours par ne plus la dire pareil. Cette page explique, et renvoie.
 *
 * LA FORME RÉPOND À UNE CONTRAINTE EXPLICITE (« synthétique même si le sujet est vaste,
 * pas indigeste, pas monotone ») : les six conditions d'un projet réussi d'abord, pour qui
 * n'ouvrira rien ; puis cinq onglets, qui évitent d'empiler huit sujets sur une page
 * interminable ; dans chaque onglet, de petites vignettes pour l'essentiel et des
 * `<details>` natifs pour le détail — le clavier, le lecteur d'écran et la recherche dans
 * la page marchent sans qu'on ait à les recoder, et le texte reste dans le document même
 * replié, donc lisible par un moteur de recherche. Chaque onglet porte sa propre teinte
 * d'icônes : c'est ce qui empêche cinq grilles de cartes de se ressembler.
 *
 * LE CONTENU VIT DANS `data/soleil.ts` — huit cents lignes de texte dans ce fichier
 * auraient noyé la mise en page. Les sections éditoriales partagées avec le pré-rendu SEO
 * restent, elles, dans `data/piliers.json` : la version servie aux moteurs dit donc la
 * même chose que la page.
 */

import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, ChevronDown, MessageSquare, Sun } from 'lucide-react'

import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useTitle } from '../hooks/useTitle'
import piliers from '../data/piliers.json'
import { CONDITIONS, REPERES, SECTIONS, type Onglet, type Section } from '../data/soleil'

const PILIER = piliers.find((p) => p.slug === 'solaire')!

/** Les classes d'icônes doivent être écrites en clair : Tailwind ne compile que ce qu'il
 *  lit dans les fichiers, une classe construite par concaténation serait absente du CSS. */
const TEINTES: Record<Section['teinte'], { fond: string; trait: string }> = {
  primary: { fond: 'bg-primary/10', trait: 'text-primary' },
  sky: { fond: 'bg-sky/10', trait: 'text-sky' },
  leaf: { fond: 'bg-leaf/10', trait: 'text-leaf' },
  terra: { fond: 'bg-terra/10', trait: 'text-terra' },
}

/* ------------------------------------------------------------------ Le détail */

/** Une question dépliable. `<details>` natif, et une seule ouverte à la fois n'est PAS
 *  imposée : sur un sujet technique, on compare souvent deux réponses côte à côte. */
function Question({ q, r }: { q: string; r: string }) {
  return (
    <details className="group border-b border-bord last:border-0">
      <summary className="flex cursor-pointer list-none items-start justify-between gap-4
        py-3.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50">
        <span className="font-semibold text-ink group-hover:text-primary">{q}</span>
        <ChevronDown className="mt-0.5 h-5 w-5 shrink-0 text-primary transition-transform
          group-open:rotate-180" />
      </summary>
      <p className="pb-4 pr-8 text-dark/75">{r}</p>
    </details>
  )
}

/* ------------------------------------------------------------- Une section */

function Contenu({ section }: { section: Section }) {
  const { fond, trait } = TEINTES[section.teinte]

  return (
    <>
      <section className="mx-auto max-w-[1100px] px-4 pb-8">
        <h2 className="font-display text-2xl text-ink md:text-3xl">{section.titreVignettes}</h2>

        {/* Petites vignettes : trois par ligne sur grand écran, et volontairement courtes.
            Ce qui ne tient pas en trois lignes descend dans les dépliants. */}
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {section.vignettes.map((v) => (
            <div key={v.titre} className="rounded-2xl border border-bord bg-white p-4">
              <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${fond}`}>
                <v.icon className={`h-5 w-5 ${trait}`} aria-hidden="true" />
              </div>
              <h3 className="mt-2.5 font-display text-lg text-ink">{v.titre}</h3>
              <p className="mt-1 text-sm text-dark/75">{v.texte}</p>
              {v.retenir && (
                <p className="mt-2 text-sm font-semibold text-primary">{v.retenir}</p>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-[900px] px-4 pb-8">
        <div className="rounded-2xl border border-bord bg-white px-5 py-1 sm:px-6">
          <h2 className="border-b border-bord py-4 font-display text-xl text-ink">
            {section.titreDeplies}
          </h2>
          {section.deplies.map((d) => (
            <Question key={d.q} q={d.q} r={d.r} />
          ))}
        </div>
      </section>

      {section.parlerVrai && (
        <section className="mx-auto max-w-[900px] px-4 pb-10">
          <div className="rounded-r-2xl border-l-4 border-primary bg-gray-50 p-5 text-gray-700">
            <strong>Le parler-vrai d’Helios.</strong> {section.parlerVrai}
          </div>
        </section>
      )}
    </>
  )
}

/* ------------------------------------------------------------------- La page */

export default function Soleil() {
  useTitle('Le soleil — matériel, pose et garanties')

  /* L'onglet vit dans l'URL : un lien peut viser directement les garanties, et un retour
     en arrière ramène là où on était. `replace` pour ne pas empiler une entrée d'historique
     à chaque clic d'onglet — c'est le choix déjà fait sur « La terre ». */
  const [params, setParams] = useSearchParams()
  const demande = params.get('sujet')
  const section = SECTIONS.find((s) => s.id === demande) ?? SECTIONS[0]

  function choisir(id: Onglet) {
    setParams(id === SECTIONS[0].id ? {} : { sujet: id }, { replace: true })
  }

  return (
    <>
      <Hero
        title="Le soleil, et ce qu’il faut regarder de près"
        subtitle={PILIER.sousTitre}
      />

      <section className="mx-auto max-w-[900px] px-4 pb-8 pt-10">
        <p className="text-lg text-dark/80">{PILIER.intro}</p>

        <ul className="mt-5 flex flex-wrap gap-x-5 gap-y-2">
          {REPERES.map((r) => (
            <li key={r.texte} className="flex items-center gap-1.5 text-sm text-dark/70">
              <r.icon className="h-4 w-4 shrink-0 text-leaf" aria-hidden="true" />
              {r.texte}
            </li>
          ))}
        </ul>
      </section>

      {/* Le résumé de toute la page, pour qui n'ouvrira aucun onglet. Carte encre : c'est
          le seul endroit du site où l'or est lisible, et il sert ici à numéroter. */}
      <section className="mx-auto max-w-[1100px] px-4 pb-10">
        <div className="rounded-2xl bg-ink p-6 sm:p-8">
          <div className="flex items-center gap-2.5">
            <Sun className="h-6 w-6 shrink-0 text-sun" aria-hidden="true" />
            <h2 className="font-display text-2xl text-sable">
              Les six conditions d’un projet réussi
            </h2>
          </div>
          <p className="mt-2 max-w-[700px] text-sable/70">
            Elles reviennent dans tous les dossiers qui se passent bien, et leur absence
            explique la plupart de ceux qui se passent mal. Le reste de cette page les détaille.
          </p>
          <ol className="mt-6 grid gap-x-8 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">
            {CONDITIONS.map((c, i) => (
              <li key={c.titre} className="flex items-start gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full
                  bg-sun/15 text-sm font-bold text-sun">{i + 1}</span>
                <span>
                  <strong className="font-semibold text-sable">{c.titre}</strong>
                  <span className="mt-0.5 block text-sm text-sable/70">{c.texte}</span>
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Les onglets. Cinq sujets sans rapport de lecture l'un avec l'autre : empilés, la
          page ferait cinq fois sa hauteur et chacun défilerait devant ce qui ne l'intéresse
          pas — même raisonnement que sur « La terre », avec cinq sujets au lieu de deux. */}
      <section className="mx-auto max-w-[1100px] px-4 pb-6">
        <div role="tablist" aria-label="Les cinq faces du solaire"
          className="flex flex-wrap gap-2">
          {SECTIONS.map(({ id, label, Icone }) => (
            <button key={id} role="tab" type="button" aria-selected={section.id === id}
              onClick={() => choisir(id)}
              className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2.5
                text-sm font-semibold transition-colors sm:text-base
                ${section.id === id
                  ? 'border-primary bg-primary text-white'
                  : 'border-ink/20 text-ink hover:border-ink hover:bg-white'}`}>
              <Icone className="h-4 w-4 shrink-0" aria-hidden="true" /> {label}
            </button>
          ))}
        </div>
        <p className="mt-3 text-dark/70">{section.phrase}</p>
      </section>

      <Contenu section={section} />

      {/* Les deux portes de sortie : le chiffrage, et la question. Comme sur « La terre ». */}
      <section className="mx-auto max-w-[900px] px-4 pb-10">
        <div className="rounded-2xl border border-primary/20 bg-primary/5 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Sun className="mt-0.5 h-7 w-7 shrink-0 text-primary" aria-hidden="true" />
              <div>
                <h2 className="font-display text-xl text-ink">
                  Voir ce que ça donne sur votre maison
                </h2>
                <p className="mt-1 max-w-[560px] text-sm text-dark/75">
                  Les panneaux sont posés dans « la maison de demain », à côté du stockage,
                  du pilotage et du reste. Vous y verrez des chiffres calculés pour votre
                  commune et votre consommation, pas des moyennes.
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
                <MessageSquare className="h-4 w-4" /> Poser ma question
              </Link>
            </div>
          </div>
        </div>
      </section>

      <FichesLiees cats={PILIER.cats} titre="Vos questions sur le solaire et le stockage" />
    </>
  )
}
