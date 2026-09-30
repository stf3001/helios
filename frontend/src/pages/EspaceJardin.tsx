/**
 * « Mon programme de cultures » — le calendrier annuel, réservé au compte et gratuit.
 *
 * C'est la contrepartie de l'inscription : le calculateur du potager est public, ce
 * programme ne l'est pas. Il n'y a rien à payer et rien de plus à remplir — la zone se
 * déduit du code postal déjà donné dans la fiche Maison.
 *
 * AUCUNE DATE N'EST ÉCRITE ICI : tout vient de `/api/jardin/programme`, qui lit le
 * fichier versionné `api/data/jardin/calendrier.json`. Un calendrier de semis est un
 * fait établi ; il se corrige en éditant ce fichier, pas en touchant à cet écran.
 *
 * LE MOIS COURANT EST LA PORTE D'ENTRÉE. Un tableau de douze colonnes est juste mais
 * inutilisable : ce qu'on veut savoir un dimanche de mars, c'est quoi semer ce mois-ci.
 * Le tableau complet reste dessous, pour ceux qui préparent leur saison.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, Home, Scissors, Shovel, Sprout } from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'
import { Skeleton } from '../components/Skeleton'
import ApiError from '../components/ApiError'

interface Legume {
  nom: string
  famille: string
  facile: boolean
  note: string
  semis_abri: number[]
  semis: number[]
  plantation: number[]
  recolte: number[]
}

interface Programme {
  zone: 'nord' | 'sud'
  zone_deduite: boolean
  version: string
  avertissement: string
  mois: { numero: number; nom: string }[]
  legumes: Legume[]
}

/** Les quatre gestes du calendrier, avec ce qui les distingue à l'œil. */
const PHASES = [
  { cle: 'semis_abri' as const, label: 'Semis à l’abri', Icone: Home, classe: 'bg-primary/60' },
  { cle: 'semis' as const, label: 'Semis en place', Icone: Sprout, classe: 'bg-leaf/70' },
  { cle: 'plantation' as const, label: 'Plantation', Icone: Shovel, classe: 'bg-primary/70' },
  { cle: 'recolte' as const, label: 'Récolte', Icone: Scissors, classe: 'bg-terra/70' },
]

export default function EspaceJardin() {
  useTitle('Mon programme de cultures')
  const { authFetch } = useAuth()
  const [programme, setProgramme] = useState<Programme | null>(null)
  const [erreur, setErreur] = useState(false)
  const [moisChoisi, setMoisChoisi] = useState(new Date().getMonth() + 1)

  const charger = useCallback(() => {
    setErreur(false)
    authFetch('/api/jardin/programme')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setProgramme)
      .catch(() => setErreur(true))
  }, [authFetch])
  useEffect(charger, [charger])

  /* Ce qu'il y a à faire le mois choisi, rangé par geste. */
  const duMois = useMemo(() => {
    if (!programme) return []
    return PHASES.map((phase) => ({
      ...phase,
      legumes: programme.legumes.filter((l) => l[phase.cle].includes(moisChoisi)),
    })).filter((p) => p.legumes.length > 0)
  }, [programme, moisChoisi])

  if (erreur) {
    return (
      <section className="mx-auto max-w-[1000px] px-4 py-12">
        <ApiError retry={charger} />
      </section>
    )
  }

  if (!programme) {
    return (
      <section className="mx-auto max-w-[1000px] px-4 py-12">
        <Skeleton className="mb-6 h-10 w-2/3" />
        <Skeleton className="h-64 w-full" />
      </section>
    )
  }

  const nomDuMois = programme.mois[moisChoisi - 1].nom

  return (
    <section className="mx-auto max-w-[1000px] px-4 py-12">
      <div className="mb-2 flex items-center gap-2">
        <CalendarDays className="h-7 w-7 text-leaf" />
        <h1 className="font-display text-2xl font-bold text-ink">Mon programme de cultures</h1>
      </div>
      <p className="mb-8 text-dark/75">
        {programme.zone_deduite ? (
          <>
            Adapté à la <strong>moitié {programme.zone}</strong> de la France, d’après le
            code postal de votre fiche Maison.
          </>
        ) : (
          <>
            Votre fiche Maison n’a pas encore de code postal : voici le programme de la{' '}
            <strong>moitié nord</strong>, la plus tardive des deux.{' '}
            <Link to="/mon-espace" className="text-primary underline">
              Renseignez votre commune
            </Link>{' '}
            pour l’ajuster.
          </>
        )}{' '}
        <Link to="/la-terre" className="text-primary underline">Comment s’y prendre →</Link>
      </p>

      {/* ---------- CE MOIS-CI ---------- */}
      <div className="mb-4 flex flex-wrap gap-1">
        {programme.mois.map((m) => (
          <button key={m.numero} type="button" onClick={() => setMoisChoisi(m.numero)}
            aria-pressed={moisChoisi === m.numero}
            className={`rounded-lg px-3 py-1.5 text-sm font-semibold capitalize transition
              ${moisChoisi === m.numero
                ? 'bg-primary text-white'
                : 'border border-ink/15 text-dark/75 hover:border-primary hover:text-primary'}`}>
            {m.nom.slice(0, 4)}
          </button>
        ))}
      </div>

      <div className="mb-10 rounded-2xl border border-ink/10 bg-white p-5 sm:p-6">
        <h2 className="font-display text-xl font-bold text-ink">
          En <span className="capitalize">{nomDuMois}</span>
        </h2>
        {duMois.length === 0 ? (
          <p className="mt-2 text-dark/75">
            Rien d’urgent ce mois-ci au potager — c’est le moment de préparer le sol, de
            commander les graines et de vider le composteur.
          </p>
        ) : (
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {duMois.map((p) => (
              <div key={p.cle}>
                <h3 className="flex items-center gap-2 font-semibold text-ink">
                  <p.Icone className="h-4 w-4 text-primary" /> {p.label}
                </h3>
                <ul className="mt-1.5 flex flex-wrap gap-1.5">
                  {p.legumes.map((l) => (
                    <li key={l.nom} title={l.note}
                      className={`rounded-full px-2.5 py-1 text-sm text-ink ${p.classe}`}>
                      {l.nom}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ---------- L'ANNÉE ENTIÈRE ---------- */}
      <h2 className="font-display text-xl font-bold text-ink">Toute l’année</h2>
      <p className="mb-3 text-sm text-dark/60">
        Une ligne par légume, une colonne par mois. Passez sur une pastille pour lire le
        conseil qui va avec.
      </p>

      <div className="overflow-x-auto rounded-xl border border-ink/10 bg-white">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <caption className="sr-only">
            Calendrier des semis, plantations et récoltes pour la moitié {programme.zone}
          </caption>
          <thead>
            <tr className="border-b border-ink/10">
              <th scope="col" className="p-2 text-left font-semibold text-ink">Légume</th>
              {programme.mois.map((m) => (
                <th key={m.numero} scope="col"
                  className="p-1 text-center text-xs font-semibold uppercase text-dark/60">
                  {m.nom.slice(0, 1)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {programme.legumes.map((l) => (
              <tr key={l.nom} className="border-b border-ink/5 last:border-0">
                <th scope="row" className="p-2 text-left font-normal text-ink">
                  {l.nom}
                  {l.facile && (
                    <span className="ml-1.5 rounded bg-leaf/15 px-1.5 py-0.5 text-[10px]
                      font-semibold uppercase text-leaf">facile</span>
                  )}
                </th>
                {programme.mois.map((m) => {
                  const actives = PHASES.filter((p) => l[p.cle].includes(m.numero))
                  return (
                    <td key={m.numero} className="p-1">
                      <div className="flex flex-col gap-0.5">
                        {actives.map((p) => (
                          <span key={p.cle}
                            title={`${l.nom} — ${p.label} en ${m.nom}. ${l.note}`}
                            className={`block h-2 rounded-full ${p.classe}`} />
                        ))}
                        {actives.length === 0 && <span className="block h-2" />}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="mt-3 flex flex-wrap gap-4">
        {PHASES.map((p) => (
          <li key={p.cle} className="flex items-center gap-1.5 text-sm text-dark/75">
            <span className={`h-2.5 w-6 rounded-full ${p.classe}`} /> {p.label}
          </li>
        ))}
      </ul>

      <p className="mt-6 text-xs text-dark/50">
        {programme.avertissement} Calendrier mis à jour le{' '}
        {new Date(programme.version).toLocaleDateString('fr-FR')}.
      </p>
    </section>
  )
}
