import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Home, MessageSquare, Sun, FileText, Zap, Handshake, Settings, Droplets, Building2, Wind, ArrowRight,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'
import { Skeleton, SkeletonCards } from '../components/Skeleton'
import ApiError from '../components/ApiError'
import HouseDocuments from '../components/fiche/HouseDocuments'

const NIVEAU_LABEL: Record<string, string> = {
  conseils_generaux: 'Conseils généraux',
  prediagnostic_qualitatif: 'Pré-diagnostic qualitatif',
  preaudit_chiffre: 'Pré-audit chiffré',
}

const SIMULATEURS = [
  { to: '/simulateur-solaire', icon: Sun, title: 'Potentiel solaire', desc: 'PV, batterie, tarifs — simulateur Revolt' },
  { to: '/potentiel-hydrique', icon: Droplets, title: 'Potentiel hydrique', desc: 'Eau atmosphérique (Hydrolia)' },
]

const AUTRES_TUILES = [
  { to: '/espace/audits', icon: FileText, title: 'Mes pré-audits', desc: 'Diagnostic chiffré' },
  { to: '/espace/energie', icon: Zap, title: "Mon contrat d'énergie", desc: 'Conseil & SOBRY' },
  { to: '/espace/mises-en-relation', icon: Handshake, title: 'Mises en relation', desc: 'Partenaires travaux' },
  { to: '/espace/pro', icon: Building2, title: 'Espace Pro', desc: 'Énergie de mon entreprise' },
]

export default function Espace() {
  useTitle('Mon espace')
  const { user, authFetch } = useAuth()
  const [house, setHouse] = useState<{ completeness_score: number; niveau: string; code_postal: string } | null>(null)
  const [lastAudit, setLastAudit] = useState<{ created_at: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    setError(false)
    Promise.all([
      // 404 = pas encore de fiche (état normal) ; toute autre erreur = service indisponible.
      authFetch('/api/houses/me').then((r) => (r.ok ? r.json() : r.status === 404 ? null : Promise.reject(new Error(String(r.status))))),
      authFetch('/api/audits').then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status))))),
    ]).then(([h, audits]) => {
      setHouse(h)
      if (audits.length > 0) setLastAudit(audits[0])
    }).catch(() => setError(true)).finally(() => setLoading(false))
  }, [authFetch])
  useEffect(load, [load])

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Bonjour {user?.prenom || ''} 👋</h1>
        <Link to="/espace/compte" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary">
          <Settings className="w-4 h-4" /> Mon compte
        </Link>
      </div>

      {loading ? (
        <>
          <Skeleton className="h-28 w-full mb-8" />
          <SkeletonCards count={6} />
        </>
      ) : error ? (
        <ApiError retry={load} />
      ) : (
        <>
          {/* Résumé maison */}
          <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6 mb-8">
            {house ? (
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="text-sm text-gray-500">Votre fiche maison ({house.code_postal})</div>
                  <div className="text-3xl font-bold text-primary my-1">{house.completeness_score}%</div>
                  <div className="text-sm text-gray-600">Niveau : {NIVEAU_LABEL[house.niveau] ?? house.niveau}</div>
                  {lastAudit && (
                    <div className="text-xs text-gray-400 mt-1">
                      Dernier pré-audit : {new Date(lastAudit.created_at).toLocaleDateString('fr-FR')}
                    </div>
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  <Link to="/mon-espace" className="rounded-xl bg-primary text-white text-sm font-semibold px-4 py-2 text-center hover:opacity-90">
                    Compléter ma fiche
                  </Link>
                  {house.completeness_score >= 70 && (
                    <Link to="/espace/audits" className="rounded-xl border border-primary text-primary text-sm font-semibold px-4 py-2 text-center hover:bg-primary/5">
                      Générer un pré-audit
                    </Link>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <img src="/brand/helios-thumbsup.png" alt="" className="h-12 w-12 object-contain" />
                  <div>
                    <p className="font-semibold text-ink">Bienvenue ! Commençons par votre logement.</p>
                    <p className="text-sm text-gray-600">3 questions suffisent — Helios s'occupe du reste.</p>
                  </div>
                </div>
                <Link to="/mon-espace" className="rounded-xl bg-primary text-white text-sm font-semibold px-5 py-2.5 hover:opacity-90 shrink-0">
                  Répondre aux 3 questions
                </Link>
              </div>
            )}
          </div>

          {/* Parler à Helios — proéminent, avec le contexte de la fiche */}
          <Link to="/espace/helios"
            className="group flex items-center justify-between gap-4 bg-ink text-white rounded-2xl p-6 mb-8 hover:opacity-95 transition">
            <div className="flex items-center gap-4">
              <img src="/brand/helios-thumbsup.png" alt="" className="h-12 w-12 object-contain shrink-0" />
              <div>
                <div className="font-display font-semibold text-lg">Une question ? Parlez à Helios</div>
                <div className="text-sm text-white/70">
                  Il connaît déjà votre fiche et vos simulations — pas besoin de tout réexpliquer.
                </div>
              </div>
            </div>
            <span className="inline-flex items-center gap-1.5 bg-primary text-white text-sm font-semibold px-4 py-2.5 rounded-xl shrink-0 group-hover:gap-2.5 transition-all">
              <MessageSquare className="w-4 h-4" /> Discuter <ArrowRight className="w-4 h-4" />
            </span>
          </Link>

          {/* Mes simulateurs */}
          <h2 className="font-semibold text-lg mb-3">Mes simulateurs</h2>
          <div className="grid sm:grid-cols-3 gap-4 mb-8">
            {SIMULATEURS.map((t) => (
              <Link key={t.to} to={t.to}
                className="border border-gray-200 rounded-2xl p-5 hover:border-primary hover:shadow-sm transition">
                <t.icon className="w-6 h-6 text-primary mb-2" />
                <div className="font-semibold">{t.title}</div>
                <div className="text-sm text-gray-500">{t.desc}</div>
              </Link>
            ))}
            <div className="border border-dashed border-gray-300 rounded-2xl p-5 opacity-60">
              <Wind className="w-6 h-6 text-gray-400 mb-2" />
              <div className="font-semibold text-gray-500">Potentiel éolien</div>
              <div className="text-sm text-gray-400">Simulateur Eolia — bientôt disponible</div>
            </div>
          </div>

          {/* Mes documents — accès direct, sans changer de page */}
          <h2 className="font-semibold text-lg mb-3">Mes documents</h2>
          <div className="mb-8">
            <HouseDocuments />
          </div>

          {/* Autres tuiles d'accès */}
          <h2 className="font-semibold text-lg mb-3">Le reste de mon espace</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link to="/mon-espace"
              className="border border-gray-200 rounded-2xl p-5 hover:border-primary hover:shadow-sm transition">
              <Home className="w-6 h-6 text-primary mb-2" />
              <div className="font-semibold">Ma fiche maison</div>
              <div className="text-sm text-gray-500">Compléter mon logement</div>
            </Link>
            {AUTRES_TUILES.map((t) => (
              <Link key={t.to} to={t.to}
                className="border border-gray-200 rounded-2xl p-5 hover:border-primary hover:shadow-sm transition">
                <t.icon className="w-6 h-6 text-primary mb-2" />
                <div className="font-semibold">{t.title}</div>
                <div className="text-sm text-gray-500">{t.desc}</div>
              </Link>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
