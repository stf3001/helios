import { AlertTriangle, CheckCircle2, Info, Wrench } from 'lucide-react'
import { Section, StatCard, useAdminData } from '../../components/admin/AdminLayout'
import { useTitle } from '../../hooks/useTitle'

interface Dashboard {
  utilisateurs: {
    total: number; nouveaux_7j: number; nouveaux_30j: number; email_verifie: number
    avec_fiche: number; completude_moyenne: number; consent_leads: number
  }
  activite: {
    conversations_7j: number; conversations_total: number; messages_7j: number
    mode_connecte_7j: number; repartition_7j: Record<string, number>; sans_reponse_7j: number
  }
  cout_ia: {
    jour_eur: number; mois_eur: number; plafond_jour_eur: number; plafond_mois_eur: number
    appels_api_mois: number; modele: string; cle_configuree: boolean; quota_par_client_jour: number
  }
  business: {
    partenaires_actifs: number; candidatures_en_attente: number; leads_total: number
    leads_par_statut: Record<string, number>; commissions_signees_mois_eur: number
    consentements_retires: number
  }
  base_connaissances: {
    fiches_actives: number; fiches_obsoletes: number; par_source: Record<string, number>; sources: number
  }
  alertes: { niveau: string; texte: string }[]
}

const VOIE_LABEL: Record<string, string> = {
  kb: 'Réponse instantanée (aucun LLM)',
  local: 'Modèle local (Ollama)',
  api: 'Claude (API, payant)',
  inconnu: 'Non renseigné',
}

function pct(n: number, total: number) {
  return total > 0 ? Math.round((n / total) * 100) : 0
}

export default function AdminDashboard() {
  useTitle('Back-office — Tableau de bord')
  const { data, error } = useAdminData<Dashboard>('/api/admin/dashboard')

  if (error) return <p className="text-rose-400">{error}</p>
  if (!data) return <p className="text-slate-500">Chargement…</p>

  const { utilisateurs: u, activite: a, cout_ia: c, business: b, base_connaissances: kb } = data
  const totalVoies = Object.values(a.repartition_7j).reduce((s, n) => s + n, 0)
  const partMois = c.plafond_mois_eur ? (c.mois_eur / c.plafond_mois_eur) * 100 : 0

  return (
    <>
      <h1 className="text-xl font-semibold text-white">Tableau de bord</h1>
      <p className="text-sm text-slate-500 mt-1">Toutes les valeurs sont lues en base — aucune estimation.</p>

      {data.alertes.length > 0 && (
        <div className="mt-5 space-y-2">
          {data.alertes.map((al, i) => {
            const Icon = al.niveau === 'alerte' ? AlertTriangle : al.niveau === 'action' ? Wrench : Info
            const couleur =
              al.niveau === 'alerte' ? 'border-rose-900/60 bg-rose-950/40 text-rose-300'
              : al.niveau === 'action' ? 'border-amber-900/60 bg-amber-950/40 text-amber-300'
              : 'border-slate-800 bg-slate-900 text-slate-400'
            return (
              <div key={i} className={'flex items-center gap-2.5 rounded-lg border px-3 py-2 text-sm ' + couleur}>
                <Icon className="w-4 h-4 shrink-0" /> {al.texte}
              </div>
            )
          })}
        </div>
      )}

      <Section title="Foyers">
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <StatCard label="Comptes" value={u.total} hint={`+${u.nouveaux_7j} sur 7 j · +${u.nouveaux_30j} sur 30 j`} />
          <StatCard label="Email vérifié" value={`${pct(u.email_verifie, u.total)} %`} hint={`${u.email_verifie} / ${u.total}`} />
          <StatCard label="Avec fiche maison" value={u.avec_fiche} hint={`${pct(u.avec_fiche, u.total)} % des comptes`} />
          <StatCard
            label="Complétude moyenne"
            value={`${u.completude_moyenne} %`}
            hint={u.completude_moyenne >= 70 ? 'Seuil pré-audit chiffré atteint' : 'Sous le seuil de 70 % du pré-audit'}
            accent={u.completude_moyenne >= 70 ? 'ok' : 'warn'}
          />
        </div>
      </Section>

      <Section title="Activité d'Helios (7 derniers jours)">
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <StatCard label="Conversations" value={a.conversations_7j} hint={`${a.conversations_total} au total`} />
          <StatCard label="Messages" value={a.messages_7j} />
          <StatCard label="Dont mode connecté" value={a.mode_connecte_7j} hint={`${pct(a.mode_connecte_7j, a.conversations_7j)} % des conversations`} />
          <StatCard
            label="Questions sans réponse"
            value={a.sans_reponse_7j}
            hint="Aucune source pertinente trouvée — à couvrir dans la base"
            accent={a.sans_reponse_7j > 0 ? 'warn' : 'ok'}
          />
        </div>

        <div className="mt-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-3">Comment Helios a répondu</div>
          {totalVoies === 0 ? (
            <p className="text-sm text-slate-500">Aucune réponse sur la période.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(a.repartition_7j)
                .sort((x, y) => y[1] - x[1])
                .map(([voie, n]) => (
                  <div key={voie} className="flex items-center gap-3 text-sm">
                    <span className="w-56 shrink-0 text-slate-400">{VOIE_LABEL[voie] ?? voie}</span>
                    <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={'h-full ' + (voie === 'api' ? 'bg-amber-500' : voie === 'kb' ? 'bg-emerald-500' : 'bg-sky-500')}
                        style={{ width: `${pct(n, totalVoies)}%` }}
                      />
                    </div>
                    <span className="w-20 text-right tabular-nums text-slate-300">{n} · {pct(n, totalVoies)} %</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      </Section>

      <Section title="Coût de l'IA">
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Aujourd'hui"
            value={`${c.jour_eur.toFixed(2)} €`}
            hint={`plafond ${c.plafond_jour_eur} €`}
            accent={c.jour_eur >= 0.8 * c.plafond_jour_eur ? 'bad' : 'ok'}
          />
          <StatCard
            label="Ce mois"
            value={`${c.mois_eur.toFixed(2)} €`}
            hint={`${Math.round(partMois)} % du plafond de ${c.plafond_mois_eur} €`}
            accent={partMois >= 80 ? 'bad' : partMois >= 50 ? 'warn' : 'ok'}
          />
          <StatCard label="Appels API ce mois" value={c.appels_api_mois} hint={`quota ${c.quota_par_client_jour}/client/jour`} />
          <StatCard
            label="Modèle"
            value={<span className="text-base">{c.cle_configuree ? c.modele : 'local uniquement'}</span>}
            hint={c.cle_configuree ? 'Clé API configurée' : 'Aucune clé — mode simplifié'}
            accent={c.cle_configuree ? 'ok' : 'warn'}
          />
        </div>
      </Section>

      <Section title="Partenaires & mises en relation">
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <StatCard label="Partenaires actifs" value={b.partenaires_actifs} />
          <StatCard
            label="Candidatures en attente"
            value={b.candidatures_en_attente}
            hint={b.candidatures_en_attente > 0 ? 'À examiner' : 'Rien à traiter'}
            accent={b.candidatures_en_attente > 0 ? 'warn' : 'ok'}
          />
          <StatCard label="Leads" value={b.leads_total} hint={Object.entries(b.leads_par_statut).map(([s, n]) => `${s} : ${n}`).join(' · ') || '—'} />
          <StatCard label="Commissions signées (mois)" value={`${b.commissions_signees_mois_eur.toFixed(2)} €`} />
        </div>
        {b.consentements_retires > 0 && (
          <p className="text-xs text-slate-500 mt-2">
            {b.consentements_retires} consentement(s) client retiré(s) — les leads concernés ne doivent plus être exploités.
          </p>
        )}
      </Section>

      <Section title="Base de connaissances">
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <StatCard label="Fiches actives" value={kb.fiches_actives} hint={`${kb.sources} sources`} />
          <StatCard
            label="Fiches obsolètes"
            value={kb.fiches_obsoletes}
            hint={kb.fiches_obsoletes > 0 ? 'Repérées par l’agent de veille' : 'Aucune'}
            accent={kb.fiches_obsoletes > 0 ? 'warn' : 'ok'}
          />
          <div className="col-span-2 rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Répartition par source</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(kb.par_source).map(([src, n]) => (
                <span key={src} className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                  {src} <span className="text-slate-500 tabular-nums">{n}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </Section>

      <p className="mt-8 flex items-center gap-1.5 text-xs text-slate-600">
        <CheckCircle2 className="w-3.5 h-3.5" /> Données lues directement en base au chargement de la page.
      </p>
    </>
  )
}
