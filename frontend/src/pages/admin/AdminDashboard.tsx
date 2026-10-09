import { AlertTriangle, CheckCircle2, Info, Wrench } from 'lucide-react'
import { Attente, Erreur, Section, StatCard, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
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

/** La couleur de la barre suit celle de la pastille « voie » des conversations. */
const VOIE_BARRE: Record<string, string> = {
  kb: 'bg-leaf',
  local: 'bg-sky',
  api: 'bg-terra',
}

function pct(n: number, total: number) {
  return total > 0 ? Math.round((n / total) * 100) : 0
}

export default function AdminDashboard() {
  useTitle('Back-office — Tableau de bord')
  const { data, error } = useAdminData<Dashboard>('/api/admin/dashboard')

  if (error) return <Erreur>{error}</Erreur>
  if (!data) return <Attente />

  const { utilisateurs: u, activite: a, cout_ia: c, business: b, base_connaissances: kb } = data
  const totalVoies = Object.values(a.repartition_7j).reduce((s, n) => s + n, 0)
  const partMois = c.plafond_mois_eur ? (c.mois_eur / c.plafond_mois_eur) * 100 : 0

  return (
    <>
      <TitrePage titre="Tableau de bord">Toutes les valeurs sont lues en base — aucune estimation.</TitrePage>

      {data.alertes.length > 0 && (
        <div className="mt-5 space-y-2">
          {data.alertes.map((al, i) => {
            const Icon = al.niveau === 'alerte' ? AlertTriangle : al.niveau === 'action' ? Wrench : Info
            const couleur =
              al.niveau === 'alerte' ? 'border-primary/40 bg-primary/5 text-primary'
              : al.niveau === 'action' ? 'border-terra/40 bg-terra/10 text-terra'
              : 'border-bord bg-white text-dark/70'
            return (
              <div key={i} className={'flex items-center gap-2.5 rounded-xl border px-3 py-2 text-sm ' + couleur}>
                <Icon className="h-4 w-4 shrink-0" /> {al.texte}
              </div>
            )
          })}
        </div>
      )}

      <Section title="Foyers">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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

        <div className="mt-3 rounded-2xl border border-bord bg-white p-4">
          <div className="mb-3 text-xs uppercase tracking-wide text-dark/55">Comment Helios a répondu</div>
          {totalVoies === 0 ? (
            <p className="text-sm text-dark/70">Aucune réponse sur la période.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(a.repartition_7j)
                .sort((x, y) => y[1] - x[1])
                .map(([voie, n]) => (
                  <div key={voie} className="flex items-center gap-3 text-sm">
                    <span className="w-56 shrink-0 text-dark/70">{VOIE_LABEL[voie] ?? voie}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-cream">
                      <div
                        className={'h-full ' + (VOIE_BARRE[voie] ?? 'bg-dark/30')}
                        style={{ width: `${pct(n, totalVoies)}%` }}
                      />
                    </div>
                    <span className="w-20 text-right tabular-nums text-dark">{n} · {pct(n, totalVoies)} %</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      </Section>

      <Section title="Coût de l'IA">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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
            value={<span className="text-xl">{c.cle_configuree ? c.modele : 'local uniquement'}</span>}
            hint={c.cle_configuree ? 'Clé API configurée' : 'Aucune clé — mode simplifié'}
            accent={c.cle_configuree ? 'ok' : 'warn'}
          />
        </div>
      </Section>

      <Section title="Partenaires & mises en relation">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
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
          <p className="mt-2 text-xs text-dark/60">
            {b.consentements_retires} consentement(s) client retiré(s) — les leads concernés ne doivent plus être exploités.
          </p>
        )}
      </Section>

      <Section title="Base de connaissances">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard label="Fiches actives" value={kb.fiches_actives} hint={`${kb.sources} sources`} />
          <StatCard
            label="Fiches obsolètes"
            value={kb.fiches_obsoletes}
            hint={kb.fiches_obsoletes > 0 ? "Repérées par l'agent de veille" : 'Aucune'}
            accent={kb.fiches_obsoletes > 0 ? 'warn' : 'ok'}
          />
          <div className="col-span-2 rounded-2xl border border-bord bg-white p-4">
            <div className="mb-2 text-xs uppercase tracking-wide text-dark/55">Répartition par source</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(kb.par_source).map(([src, n]) => (
                <span key={src} className="rounded-full border border-bord bg-cream px-2.5 py-1 text-xs text-dark">
                  {src} <span className="tabular-nums text-dark/55">{n}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </Section>

      <p className="mt-8 flex items-center gap-1.5 text-xs text-dark/50">
        <CheckCircle2 className="h-3.5 w-3.5" /> Données lues directement en base au chargement de la page.
      </p>
    </>
  )
}
