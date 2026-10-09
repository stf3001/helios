import { useState } from 'react'
import { BadgeCheck, Copy, Globe2, MapPin, Pause, Play } from 'lucide-react'
import Depliant from '../../components/Depliant'
import {
  Attente, BTN_PRIMAIRE, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData,
} from '../../components/admin/AdminLayout'
import { REGIONS, regionsDesZones } from '../../data/regions'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Partner {
  id: string
  raison_sociale: string
  siret: string | null
  email: string | null
  rge: boolean
  zones: string[] | null
  metiers: string[] | null
  statut: string
  note_moyenne: number | null
  charte_signee_at: string | null
  created_at: string
}

const STATUT_STYLE: Record<string, string> = {
  candidat: 'border-terra/40 bg-terra/10 text-terra',
  en_attente: 'border-bord bg-cream text-dark/70',
  actif: 'border-leaf/40 bg-leaf/10 text-leaf',
  suspendu: 'border-primary/40 bg-primary/10 text-primary',
}

const STATUT_LABEL: Record<string, string> = {
  candidat: 'candidature',
  en_attente: 'en attente',
  actif: 'actif',
  suspendu: 'suspendu',
}

/** Un groupe affiché : une région, les acteurs nationaux, ou les zones non renseignées. */
interface Groupe {
  cle: string
  nom: string
  national?: boolean
  partenaires: Partner[]
}

/**
 * Range les partenaires par région (demande de Stéphane, 08/10/2026).
 *
 * Avant, la page listait une centaine de lignes à plat : depuis que l'annuaire est semé
 * région par région, c'était illisible et on ne voyait plus le seul chiffre qui compte —
 * combien d'entreprises RÉELLEMENT actives couvrent tel territoire.
 *
 * Deux cas sortent de la grille régionale : les acteurs nationaux (eau, éolien, inertie,
 * courtage : ils vendent à distance et couvrent les 13 régions — les répéter 13 fois
 * noierait les autres), et les partenaires sans zone déclarée, qu'il ne faut pas perdre.
 * Un partenaire multirégional sans être national — Ensol couvre tout sauf PACA — apparaît
 * bien dans chacune de ses régions : c'est la vérité de sa couverture.
 */
function grouperParRegion(partenaires: Partner[]): Groupe[] {
  const parRegion = new Map<string, Partner[]>(REGIONS.map((r) => [r.code, []]))
  const nationaux: Partner[] = []
  const sansZone: Partner[] = []

  for (const p of partenaires) {
    const codes = regionsDesZones(p.zones)
    if (codes.length === 0) sansZone.push(p)
    else if (codes.length === REGIONS.length) nationaux.push(p)
    else for (const code of codes) parRegion.get(code)!.push(p)
  }

  const groupes: Groupe[] = REGIONS.map((r) => ({
    cle: r.code, nom: r.nom, partenaires: parRegion.get(r.code)!,
  }))
  if (nationaux.length) {
    groupes.unshift({ cle: '_national', nom: 'Toute la France', national: true, partenaires: nationaux })
  }
  if (sansZone.length) {
    groupes.push({ cle: '_sans_zone', nom: 'Zone non renseignée', partenaires: sansZone })
  }
  return groupes
}

export default function AdminPartenaires() {
  useTitle('Back-office — Partenaires')
  const { authFetch } = useAuth()
  const { data, error, reload } = useAdminData<Partner[]>('/api/admin/partners')
  const [busy, setBusy] = useState<string | null>(null)
  // Le mot de passe initial n'est renvoyé qu'UNE fois par l'API : on le garde à l'écran
  // jusqu'à ce que l'admin l'ait transmis au partenaire.
  const [motDePasse, setMotDePasse] = useState<{ email: string; mdp: string } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function agir(p: Partner, action: 'activate' | 'suspend') {
    if (action === 'suspend' && !confirm(`Suspendre ${p.raison_sociale} ? Il n'apparaîtra plus dans l'annuaire public.`)) return
    setBusy(p.id)
    setActionError(null)
    try {
      const r = await authFetch(`/api/admin/partners/${p.id}/${action}`, { method: 'POST' })
      if (!r.ok) throw new Error(`Erreur ${r.status}`)
      const body = await r.json()
      if (action === 'activate' && body.mot_de_passe_initial) {
        setMotDePasse({ email: body.email, mdp: body.mot_de_passe_initial })
      }
      reload()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Action impossible')
    } finally {
      setBusy(null)
    }
  }

  if (error) return <Erreur>{error}</Erreur>
  if (!data) return <Attente />

  // Les candidatures spontanées passent avant la carte : ce sont les seules qui attendent
  // une décision. Les « en attente » du seed, eux, attendent une signature commerciale.
  const candidats = data.filter((p) => p.statut === 'candidat')
  const groupes = grouperParRegion(data.filter((p) => p.statut !== 'candidat'))
  const actifs = data.filter((p) => p.statut === 'actif').length

  return (
    <>
      <TitrePage titre="Partenaires">
        Activer une candidature signe la charte et génère l'accès à l'espace partenaire.
        <strong className="font-semibold text-ink"> {actifs} partenaire(s) actif(s)</strong> sur {data.length} —
        seuls les actifs apparaissent dans l'annuaire public et peuvent être nommés par Helios.
      </TitrePage>

      {actionError && <Erreur>{actionError}</Erreur>}

      {motDePasse && (
        <div className="mt-5 rounded-2xl border border-leaf/40 bg-leaf/5 p-4">
          <div className="font-display text-lg text-ink">Accès créé — à transmettre maintenant</div>
          <p className="mt-1 text-sm text-dark/70">
            Ce mot de passe n'est affiché qu'une seule fois : il n'est pas stocké en clair.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-sm">
            <span className="rounded-lg bg-white px-2 py-1 text-dark">{motDePasse.email}</span>
            <span className="rounded-lg bg-white px-2 py-1 font-semibold text-ink">{motDePasse.mdp}</span>
            <button onClick={() => navigator.clipboard?.writeText(motDePasse.mdp)} className={BTN_SECONDAIRE}>
              <Copy className="h-3.5 w-3.5" /> Copier
            </button>
            <button onClick={() => setMotDePasse(null)} className="text-sm text-dark/60 underline hover:text-ink">
              J'ai transmis
            </button>
          </div>
        </div>
      )}

      {candidats.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-terra">
            Candidatures à examiner ({candidats.length})
          </h2>
          <div className="space-y-2">
            {candidats.map((p) => (
              <Ligne key={p.id} p={p} busy={busy === p.id} onAgir={agir} />
            ))}
          </div>
        </section>
      )}

      <section className="mt-8">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-dark/55">
          L'annuaire, région par région
        </h2>
        <div className="grid gap-3 lg:grid-cols-2">
          {groupes.map((g) => {
            const nbActifs = g.partenaires.filter((p) => p.statut === 'actif').length
            return (
              <Depliant
                key={g.cle}
                titre={g.nom}
                icone={
                  g.national
                    ? <Globe2 className="h-5 w-5 shrink-0 text-sky" />
                    : <MapPin className="h-5 w-5 shrink-0 text-primary" />
                }
                resume={
                  g.partenaires.length === 0 ? (
                    <span className="text-terra">aucun partenaire</span>
                  ) : (
                    <span className="flex items-center gap-1.5">
                      <span className={nbActifs > 0 ? 'font-semibold text-leaf' : 'text-terra'}>
                        {nbActifs} actif(s)
                      </span>
                      <span className="text-dark/45">sur {g.partenaires.length}</span>
                    </span>
                  )
                }
              >
                {g.partenaires.length === 0 ? (
                  <p className="text-sm text-dark/70">
                    Aucun partenaire sur cette région. Helios le dit franchement au visiteur plutôt
                    que de le renvoyer vers une région voisine.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {[...g.partenaires]
                      // Les actifs d'abord : c'est ce que le visiteur verra de cette région.
                      .sort((a, b) => Number(b.statut === 'actif') - Number(a.statut === 'actif')
                        || a.raison_sociale.localeCompare(b.raison_sociale, 'fr'))
                      .map((p) => (
                        <Ligne key={p.id} p={p} busy={busy === p.id} onAgir={agir} />
                      ))}
                  </div>
                )}
              </Depliant>
            )
          })}
        </div>
      </section>
    </>
  )
}

function Ligne({
  p, busy, onAgir,
}: { p: Partner; busy: boolean; onAgir: (p: Partner, a: 'activate' | 'suspend') => void }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-bord bg-cream/50 p-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-ink">{p.raison_sociale}</span>
          <span className={'rounded-full border px-2 py-0.5 text-xs ' + (STATUT_STYLE[p.statut] ?? 'border-bord text-dark/60')}>
            {STATUT_LABEL[p.statut] ?? p.statut}
          </span>
          {p.rge && (
            <span className="flex items-center gap-1 text-xs text-sky" title="Reconnu Garant de l'Environnement">
              <BadgeCheck className="h-3.5 w-3.5" /> RGE
            </span>
          )}
          {p.note_moyenne != null && (
            <span className={'text-xs ' + (p.note_moyenne < 3 ? 'text-primary' : 'text-dark/60')}>
              {p.note_moyenne.toFixed(1)}/5
            </span>
          )}
        </div>
        <div className="mt-1 truncate text-xs text-dark/60">
          {p.email ?? 'sans email'}
          {p.siret && <> · SIRET {p.siret}</>}
          {p.metiers?.length ? <> · {p.metiers.join(', ')}</> : null}
          {p.zones?.length ? <> · {p.zones.length} département(s)</> : null}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {p.statut !== 'actif' && (
          <button disabled={busy} onClick={() => onAgir(p, 'activate')} className={BTN_PRIMAIRE}>
            <Play className="h-3.5 w-3.5" /> {p.statut === 'candidat' ? 'Valider' : 'Activer'}
          </button>
        )}
        {p.statut === 'actif' && (
          <button disabled={busy} onClick={() => onAgir(p, 'suspend')} className={BTN_SECONDAIRE}>
            <Pause className="h-3.5 w-3.5" /> Suspendre
          </button>
        )}
      </div>
    </div>
  )
}
