import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Hero from '../components/Hero'

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
  const [partners, setPartners] = useState<PartnerCard[]>([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    fetch('/api/partners')
      .then((r) => (r.ok ? r.json() : []))
      .then(setPartners)
      .finally(() => setLoaded(true))
  }, [])

  return (
    <>
      <Hero title="Des entreprises choisies, une charte exigeante." />
      <section className="max-w-[800px] mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold mb-6">La charte partenaire</h2>
        <ul className="space-y-3">
          {engagements.map((e, i) => (
            <li key={i} className="flex gap-3 text-gray-700">
              <span className="text-primary font-bold">✓</span> {e}
            </li>
          ))}
        </ul>
        <div className="mt-10 border-l-4 border-primary bg-gray-50 rounded-r-2xl p-6 text-gray-700">
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
                    <div className="text-sm text-amber-600 shrink-0">★ {p.note_moyenne}</div>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {p.rge && <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">RGE</span>}
                  {p.metiers.map((m) => (
                    <span key={m} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
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
