import { useState } from 'react'
import { BadgeCheck, Copy, FileText, Globe2, Link2, MapPin, Pause, Play, X } from 'lucide-react'
import Depliant from '../../components/Depliant'
import {
  Attente, BTN_DANGER, BTN_PRIMAIRE, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData,
} from '../../components/admin/AdminLayout'
import { ETAT_JUSTIFICATIF, LIBELLE_JUSTIFICATIF, dateCourte } from '../../components/mer/libelles'
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
  demo?: boolean  // partenaire de démonstration (point 60) : visible du seul compte de démo
  motif_refus: string | null
  charte_version_signee: string | null
  charte_en_vigueur: string | null
  compte_active: boolean
  en_regle: boolean
  justificatifs: Record<string, { etat: string; date_fin: string | null }>
  documents: Doc[]
  created_at: string
}
interface Doc {
  id: string; type: string; filename: string; date_delivrance: string | null; date_fin: string | null
  statut: string; motif_refus: string | null; created_at: string
}
interface Echeance { partner_id: string; raison_sociale: string; demo: boolean; libelle: string; etat: string; date_fin: string | null }

const STATUT_STYLE: Record<string, string> = {
  candidat: 'border-terra/40 bg-terra/10 text-terra',
  en_attente: 'border-bord bg-cream text-dark/70',
  actif: 'border-leaf/40 bg-leaf/10 text-leaf',
  suspendu: 'border-primary/40 bg-primary/10 text-primary',
  refuse: 'border-bord bg-sable text-dark/60',
}

const STATUT_LABEL: Record<string, string> = {
  candidat: 'candidature',
  en_attente: 'en attente',
  actif: 'actif',
  suspendu: 'suspendu',
  refuse: 'refusée',
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
  const echeances = useAdminData<Echeance[]>('/api/admin/justificatifs/echeances')
  const [busy, setBusy] = useState<string | null>(null)
  // Le lien d'activation n'est montré qu'une fois (seul son haché est stocké) : il reste à
  // l'écran jusqu'à ce que l'administration l'ait transmis. Aucun e-mail ne part.
  const [lien, setLien] = useState<{ raison: string; email: string | null; url: string; expire: string } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function appeler(p: Partner, chemin: string, corps?: object) {
    setBusy(p.id)
    setActionError(null)
    try {
      const r = await authFetch(`/api/admin/partners/${p.id}/${chemin}`, {
        method: 'POST', ...(corps ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) } : {}),
      })
      const body = await r.json().catch(() => null)
      if (!r.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : `Erreur ${r.status}`)
      if (body?.lien) {
        setLien({ raison: p.raison_sociale, email: body.email, url: window.location.origin + body.lien, expire: body.expire_le })
      }
      reload(); echeances.reload()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Action impossible')
    } finally {
      setBusy(null)
    }
  }

  function agir(p: Partner, action: 'activate' | 'suspend' | 'lien-activation' | 'refuser') {
    if (action === 'suspend' && !confirm(`Suspendre ${p.raison_sociale} ? Il n'apparaîtra plus dans l'annuaire public.`)) return
    if (action === 'refuser') {
      const motif = prompt(`Motif du refus de la candidature de ${p.raison_sociale} :`)
      if (motif && motif.trim().length >= 3) appeler(p, 'refuser', { motif })
      return
    }
    appeler(p, action)
  }

  async function ouvrirDocument(p: Partner, d: Doc) {
    const r = await authFetch(`/api/admin/partners/${p.id}/documents/${d.id}`)
    if (!r.ok) { setActionError(`Erreur ${r.status}`); return }
    window.open(URL.createObjectURL(await r.blob()), '_blank')
  }

  function refuserDocument(p: Partner, d: Doc) {
    const motif = prompt(`Motif du refus de « ${d.filename} » (le partenaire le verra) :`)
    if (motif && motif.trim().length >= 3) appeler(p, `documents/${d.id}/refuser`, { motif })
  }

  const actionsDoc = { ouvrir: ouvrirDocument, refuser: refuserDocument }

  if (error) return <Erreur>{error}</Erreur>
  if (!data) return <Attente />

  // Les candidatures spontanées passent avant la carte : ce sont les seules qui attendent
  // une décision. Les « en attente » du seed, eux, attendent une signature commerciale.
  const candidats = data.filter((p) => p.statut === 'candidat')
  const groupes = grouperParRegion(data.filter((p) => p.statut !== 'candidat' && p.statut !== 'refuse'))
  const refuses = data.filter((p) => p.statut === 'refuse')
  const charte = data[0]?.charte_en_vigueur ?? null
  const actifs = data.filter((p) => p.statut === 'actif').length

  return (
    <>
      <TitrePage titre="Partenaires">
        Valider une candidature donne un lien d'activation à transmettre vous-même : le partenaire y
        choisit son mot de passe, puis signe la charte dans son espace.
        {charte ? <> Charte en vigueur : <strong className="font-semibold text-ink">{charte}</strong>.</>
          : <strong className="font-semibold text-terra"> Aucune charte en vigueur : personne n'est proposé aux foyers.</strong>}
        <strong className="font-semibold text-ink"> {actifs} partenaire(s) actif(s)</strong> sur {data.length} —
        seuls les actifs apparaissent dans l'annuaire public et peuvent être nommés par Helios.
      </TitrePage>

      {actionError && <Erreur>{actionError}</Erreur>}

      {lien && (
        <div className="mt-5 rounded-2xl border border-leaf/40 bg-leaf/5 p-4">
          <div className="font-display text-lg text-ink">Lien d'activation de {lien.raison} — à transmettre maintenant</div>
          <p className="mt-1 text-sm text-dark/70">
            À envoyer vous-même à {lien.email ?? 'ce partenaire'}. Valable une seule fois, jusqu'au {dateCourte(lien.expire)} ;
            il n'est affiché qu'ici, et un nouveau lien annule celui-ci.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="min-w-0 max-w-full break-all rounded-lg bg-white px-2 py-1 font-mono text-xs text-ink">{lien.url}</span>
            <button onClick={() => navigator.clipboard?.writeText(lien.url)} className={BTN_SECONDAIRE}>
              <Copy className="h-3.5 w-3.5" /> Copier
            </button>
            <button onClick={() => setLien(null)} className="text-sm text-dark/60 underline hover:text-ink">
              J'ai transmis
            </button>
          </div>
        </div>
      )}

      {echeances.data && echeances.data.length > 0 && (
        <section className="mt-8">
          <Depliant titre="Justificatifs expirés ou à échéance dans 30 jours" ouvert
            icone={<FileText className="h-5 w-5 shrink-0 text-terra" />}
            resume={<span className="text-terra">{echeances.data.length} à suivre</span>}>
            <ul className="space-y-1 text-sm">
              {echeances.data.map((e) => (
                <li key={`${e.partner_id}-${e.libelle}`} className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-ink">{e.raison_sociale}</span>
                  {e.demo && <span className="text-xs text-dark/55">(Démo)</span>}
                  <span className="text-dark/70">{e.libelle}</span>
                  <span className={'rounded-full border px-2 py-0.5 text-xs ' + ETAT_JUSTIFICATIF[e.etat].style}>
                    {ETAT_JUSTIFICATIF[e.etat].label}{e.date_fin && ` · ${dateCourte(e.date_fin)}`}
                  </span>
                </li>
              ))}
            </ul>
          </Depliant>
        </section>
      )}

      {candidats.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-terra">
            Candidatures à examiner ({candidats.length})
          </h2>
          <div className="space-y-2">
            {candidats.map((p) => (
              <Ligne key={p.id} p={p} busy={busy === p.id} onAgir={agir} docs={actionsDoc} />
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
                        <Ligne key={p.id} p={p} busy={busy === p.id} onAgir={agir} docs={actionsDoc} />
                      ))}
                  </div>
                )}
              </Depliant>
            )
          })}
        </div>
      </section>

      {refuses.length > 0 && (
        <section className="mt-8">
          <Depliant titre="Candidatures refusées" resume={<span className="text-dark/55">{refuses.length}</span>}>
            <ul className="space-y-1 text-sm">
              {refuses.map((p) => (
                <li key={p.id}><span className="font-semibold text-ink">{p.raison_sociale}</span>
                  <span className="text-dark/60"> — {p.motif_refus}</span></li>
              ))}
            </ul>
          </Depliant>
        </section>
      )}
    </>
  )
}

type ActionsDoc = { ouvrir: (p: Partner, d: Doc) => void; refuser: (p: Partner, d: Doc) => void }

function Ligne({
  p, busy, onAgir, docs,
}: {
  p: Partner; busy: boolean; docs: ActionsDoc
  onAgir: (p: Partner, a: 'activate' | 'suspend' | 'lien-activation' | 'refuser') => void
}) {
  const [voirDocs, setVoirDocs] = useState(p.statut === 'candidat')
  return (
    <div className="rounded-xl border border-bord bg-cream/50 p-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-ink">{p.raison_sociale}</span>
            {p.demo && (
              <span className="rounded-full border border-bord bg-sable px-2 py-0.5 text-xs text-dark/60"
                title="Visible du seul compte de démo, jamais dans l'annuaire public">Démo</span>
            )}
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
          {p.statut === 'actif' && (
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs">
              <span className={p.en_regle ? 'text-leaf' : 'text-terra'}>
                {p.en_regle ? 'Proposé aux foyers' : 'Pas proposé aux foyers'}
              </span>
              <span className={p.charte_version_signee && p.charte_version_signee === p.charte_en_vigueur ? 'text-dark/60' : 'text-terra'}>
                {p.charte_version_signee
                  ? `Charte ${p.charte_version_signee} signée le ${dateCourte(p.charte_signee_at)}`
                  : 'Charte non signée'}
              </span>
              {!p.compte_active && <span className="text-terra">Compte jamais activé</span>}
            </div>
          )}
          <div className="mt-1 flex flex-wrap gap-1.5">
            {Object.entries(p.justificatifs).map(([t, e]) => (
              <span key={t} className={'rounded-full border px-2 py-0.5 text-xs ' + ETAT_JUSTIFICATIF[e.etat].style}>
                {LIBELLE_JUSTIFICATIF[t]} : {ETAT_JUSTIFICATIF[e.etat].label}{e.date_fin && ` (${dateCourte(e.date_fin)})`}
              </span>
            ))}
            {p.documents.length > 0 && (
              <button onClick={() => setVoirDocs(!voirDocs)} className="text-xs text-dark/60 underline hover:text-ink">
                {voirDocs ? 'Masquer' : 'Voir'} les {p.documents.length} pièce(s)
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {p.statut === 'candidat' && (
            <>
              <button disabled={busy} onClick={() => onAgir(p, 'activate')} className={BTN_PRIMAIRE}>
                <Play className="h-3.5 w-3.5" /> Valider
              </button>
              <button disabled={busy} onClick={() => onAgir(p, 'refuser')} className={BTN_DANGER}>
                <X className="h-3.5 w-3.5" /> Refuser
              </button>
            </>
          )}
          {p.statut === 'suspendu' && (
            <button disabled={busy} onClick={() => onAgir(p, 'activate')} className={BTN_PRIMAIRE}>
              <Play className="h-3.5 w-3.5" /> Réactiver
            </button>
          )}
          {p.statut === 'actif' && (
            <>
              <button disabled={busy} onClick={() => onAgir(p, 'lien-activation')} className={BTN_SECONDAIRE}
                title="Pour un premier accès, un lien expiré ou un mot de passe oublié">
                <Link2 className="h-3.5 w-3.5" /> Lien d'activation
              </button>
              <button disabled={busy} onClick={() => onAgir(p, 'suspend')} className={BTN_SECONDAIRE}>
                <Pause className="h-3.5 w-3.5" /> Suspendre
              </button>
            </>
          )}
        </div>
      </div>
      {voirDocs && p.documents.length > 0 && (
        <ul className="mt-2 space-y-1 border-t border-bord pt-2 text-xs">
          {p.documents.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center gap-2">
              <button onClick={() => docs.ouvrir(p, d)} className="flex items-center gap-1 text-ink underline">
                <FileText className="h-3.5 w-3.5" /> {LIBELLE_JUSTIFICATIF[d.type]} — {d.filename}
              </button>
              <span className="text-dark/60">
                {d.date_delivrance && `délivré le ${dateCourte(d.date_delivrance)}`}
                {d.date_fin && `valable jusqu'au ${dateCourte(d.date_fin)}`} · déposé le {dateCourte(d.created_at)}
              </span>
              {d.statut === 'refuse'
                ? <span className="text-primary">refusé : {d.motif_refus}</span>
                : <button onClick={() => docs.refuser(p, d)} className="text-primary underline">Refuser</button>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
