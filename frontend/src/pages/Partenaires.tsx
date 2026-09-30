import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, Star } from 'lucide-react'
import Hero from '../components/Hero'
import { useTitle } from '../hooks/useTitle'
import ApiError from '../components/ApiError'

const engagements = [
  'Certifications à jour (RGE quand les aides l\'exigent), assurance décennale',
  'Transparence des prix : devis détaillés, sans frais cachés, délais tenus',
  'Aucun démarchage hors demande explicite, pas de vente forcée',
  'Travaux conformes aux règles de l\'art, SAV réactif',
  'Acceptation de la notation par les clients',
  'Un partenaire qui ne respecte plus la charte est déréférencé — sans exception',
]

const METIER_LABEL: Record<string, string> = {
  pv: 'Photovoltaïque', pac: 'Pompe à chaleur', isolation: 'Isolation',
  menuiseries: 'Menuiseries', vmc: 'Ventilation', regulation: 'Régulation',
}

interface PartnerCard {
  id: string
  raison_sociale: string
  rge: boolean
  zones: string[]
  metiers: string[]
  note_moyenne: number | null
}

export default function Partenaires() {
  useTitle('Nos partenaires')
  const [partners, setPartners] = useState<PartnerCard[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  const load = useCallback(() => {
    setLoaded(false)
    setError(false)
    fetch('/api/partners')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setPartners)
      .catch(() => setError(true))
      .finally(() => setLoaded(true))
  }, [])
  useEffect(load, [load])

  return (
    <>
      <Hero title="Des entreprises choisies, une charte exigeante." />
      <section className="max-w-[800px] mx-auto px-4 py-12">
        <h2 className="font-display text-3xl mb-6">La charte partenaire</h2>
        <ul className="space-y-3">
          {engagements.map((e, i) => (
            <li key={i} className="flex items-start gap-3 text-gray-600">
              <Check className="mt-0.5 w-4 h-4 shrink-0 text-leaf" aria-hidden="true" /> {e}
            </li>
          ))}
        </ul>
        <div className="mt-10 border-l-2 border-primary bg-white border-y border-r border-bord rounded-r-2xl p-6 text-gray-600">
          <strong>Transparence.</strong> Les partenaires versent à HELIOS une commission d'apport d'affaires
          quand un client leur confie des travaux via la plateforme. Cette commission ne modifie jamais les
          préconisations d'Helios, et n'est jamais facturée au client.
        </div>
      </section>

      <section className="max-w-[900px] mx-auto px-4 pb-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Nos partenaires référencés</h2>
          <Link to="/devenir-partenaire" className="text-sm text-primary underline">Devenir partenaire →</Link>
        </div>
        {!loaded ? (
          <p className="text-gray-400">Chargement…</p>
        ) : error ? (
          <ApiError retry={load} />
        ) : partners.length === 0 ? (
          <p className="text-gray-500">
            Aucun partenaire référencé pour l'instant. Vous êtes un professionnel ?{' '}
            <Link to="/devenir-partenaire" className="text-primary underline">Rejoignez-nous</Link>.
          </p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4">
            {partners.map((p) => (
              <div key={p.id} className="border border-gray-200 rounded-2xl p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="font-semibold">{p.raison_sociale}</div>
                  {p.note_moyenne != null && (
                    <div className="inline-flex items-center gap-1 text-sm text-primary shrink-0">
                      <Star className="w-3.5 h-3.5 fill-current" aria-hidden="true" /> {p.note_moyenne}
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {p.rge && <span className="text-xs bg-leaf/10 text-leaf px-2 py-0.5 rounded-full">RGE</span>}
                  {p.metiers.map((m) => (
                    <span key={m} className="text-xs bg-cream text-gray-600 px-2 py-0.5 rounded-full">
                      {METIER_LABEL[m] ?? m}
                    </span>
                  ))}
                </div>
                {p.zones.length > 0 && (
                  <div className="text-xs text-gray-400 mt-2">Zones : {p.zones.join(', ')}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  )
}
