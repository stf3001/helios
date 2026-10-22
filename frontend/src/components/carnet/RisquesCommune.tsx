import { useCallback, useEffect, useState } from 'react'
import { ExternalLink, Landmark, PenLine } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { faqSlug } from '../../lib/faqSlug'
import { ouvrirJournal } from './commun'

/**
 * « Les risques de ma commune » (phase 2), dans « Ma maison ».
 *
 * Sobre par décision : une ligne par risque recensé par Géorisques, le lien vers sa question de
 * `kb/risques_maison.md`, la date de collecte et le rapport officiel. Ni pourcentage, ni niveau,
 * ni rouge. À l'échelle de la COMMUNE : Hélios ne demande jamais l'adresse.
 * Si Géorisques ne répond pas, la section ne s'affiche pas (l'API le dit, l'écran se tait).
 */
interface Risques {
  disponible: boolean; raison?: string
  commune?: string; risques?: { code: string; libelle: string; question: string }[]
  url_rapport?: string | null; collecte_le?: string; mention?: string; question_generale?: string
  debroussaillement?: { libelle: string; lien: string | null } | null
  fissure?: { question: string } | null
}
interface Communes { code_postal: string; communes: { code_insee: string; nom: string }[]; choisie: string | null }

const lienFiche = (question: string) => `/faq/${faqSlug(question)}`

export function ChoixCommune({ onChoisie }: { onChoisie: () => void }) {
  const { authFetch } = useAuth()
  const [liste, setListe] = useState<Communes | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [choix, setChoix] = useState('')

  useEffect(() => {
    authFetch('/api/houses/me/communes').then(async (r) => {
      if (!r.ok) throw new Error()
      const b: Communes = await r.json()
      setListe(b); setChoix(b.choisie ?? (b.communes.length === 1 ? b.communes[0].code_insee : ''))
    }).catch(() => setErreur('La liste des communes est momentanément indisponible.'))
  }, [authFetch])

  async function valider() {
    const r = await authFetch('/api/houses/me/commune', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code_insee: choix }),
    })
    if (r.ok) onChoisie(); else setErreur('Commune non enregistrée : réessayez.')
  }

  if (erreur) return <p className="text-sm text-dark/60">{erreur}</p>
  if (!liste) return null
  return (
    <div className="flex flex-wrap items-end gap-2 text-sm">
      <label className="min-w-0">Votre commune ({liste.code_postal})
        <select value={choix} onChange={(e) => setChoix(e.target.value)}
          className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 sm:w-72">
          <option value="">— choisir —</option>
          {liste.communes.map((c) => <option key={c.code_insee} value={c.code_insee}>{c.nom}</option>)}
        </select>
      </label>
      <button onClick={valider} disabled={!choix}
        className="rounded-lg bg-primary px-3.5 py-2 font-semibold text-white hover:opacity-90 disabled:opacity-40">
        Enregistrer
      </button>
    </div>
  )
}

export default function RisquesCommune() {
  const { authFetch } = useAuth()
  const [r, setR] = useState<Risques | null>(null)
  const charger = useCallback(() => {
    authFetch('/api/houses/me/risques').then((x) => (x.ok ? x.json() : null)).then(setR).catch(() => setR(null))
  }, [authFetch])
  useEffect(charger, [charger])

  if (!r || (!r.disponible && r.raison !== 'commune_absente')) return null  // panne : on se tait

  return (
    <section id="risques-commune" className="scroll-mt-20 rounded-xl border border-ink/10 bg-white p-4">
      <h2 className="mb-2 flex items-center gap-2 font-display text-xl text-ink">
        <Landmark className="h-5 w-5 text-primary" /> Les risques de ma commune
      </h2>
      {!r.disponible ? (
        <>
          <p className="mb-2 text-sm text-dark/70">
            Choisissez votre commune : Hélios vous dira quels risques y sont recensés (inondation, argiles, feux de forêt…).
            Il ne vous demande pas votre adresse.
          </p>
          <ChoixCommune onChoisie={charger} />
        </>
      ) : (
        <>
          <p className="text-sm text-dark/70">
            À <strong className="text-ink">{r.commune}</strong>, Géorisques recense :
          </p>
          <ul className="mt-2 divide-y divide-bord text-sm">
            {r.risques!.map((x) => (
              <li key={x.code} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 py-2">
                <span className="text-ink">{x.libelle}</span>
                <Link to={lienFiche(x.question)} className="text-xs text-primary hover:underline">Que faire ?</Link>
              </li>
            ))}
          </ul>
          {r.risques!.length === 0 && <p className="mt-2 text-sm text-dark/70">Aucun risque recensé.</p>}

          {r.debroussaillement && (
            <p className="mt-3 rounded-lg border border-bord bg-cream/60 px-3 py-2 text-sm text-ink">
              Feux de forêt : {r.debroussaillement.libelle.toLowerCase()} par l'obligation de débroussaillement.{' '}
              <Link to="/mon-espace" className="font-semibold text-primary hover:underline">Répondre dans ma fiche</Link>
              {r.debroussaillement.lien && <>{' · '}<a href={r.debroussaillement.lien} target="_blank" rel="noreferrer"
                className="text-primary hover:underline">vérifier</a></>}
            </p>
          )}
          {r.fissure && (
            <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-dark/80">
              Sol argileux : une fissure se surveille dans le temps.
              <button onClick={() => ouvrirJournal({ type: 'autre', titre: 'Fissure constatée', intervenant: 'moi',
                note: 'Photo avec une règle à côté ; la comparer d\'une saison à l\'autre.' })}
                className="inline-flex items-center gap-1 rounded-lg border border-primary px-2.5 py-1 text-xs font-semibold text-primary hover:bg-primary/5">
                <PenLine className="h-3.5 w-3.5" /> Noter une fissure
              </button>
              <Link to={lienFiche(r.fissure.question)} className="text-xs text-primary hover:underline">Quand s'inquiéter ?</Link>
            </p>
          )}

          <p className="mt-3 text-xs text-dark/60">
            {r.mention} Données Géorisques collectées le {new Date(r.collecte_le!).toLocaleDateString('fr-FR')}.
          </p>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {r.url_rapport && (
              <a href={r.url_rapport} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
                Rapport Géorisques de la commune <ExternalLink className="h-3 w-3" />
              </a>
            )}
            <Link to={lienFiche(r.question_generale!)} className="text-primary hover:underline">Comprendre ces risques</Link>
          </div>
        </>
      )}
    </section>
  )
}
