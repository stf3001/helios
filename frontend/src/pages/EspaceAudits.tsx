import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Download } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import ApiError from '../components/ApiError'
import Depliant from '../components/Depliant'
import { faqSlug } from '../lib/faqSlug'

interface Fourchette { bas: number; haut: number; central: number }
interface Plage { bas: number; haut: number }
interface Priorite {
  rang: number
  label: string
  poste: string
  part_deperdition_pct: number | null
  cout_eur: { bas: number; haut: number }
  // v1 : un nombre ; v2 : une fourchette selon les revenus.
  aide_estimee_eur: number | Plage
  reste_a_charge_eur: number | Plage
  economie_annuelle_eur: Fourchette
  temps_retour_ans: number | null
  horizon?: 'maintenant' | 'prioritaire' | 'a_l_occasion'
  libelle_occasion?: string | null
  // v2.1
  categorie?: 'chauffage' | 'eau_chaude' | 'production'
  contexte?: string | null
  aide_note?: string | null
  base_cout?: 'surcout' | 'cout_complet'
  source?: string
  mention?: string | null
  // v2.4 : textes des fiches kb/action_* (aucun chiffre ajouté)
  pourquoi?: string | null
  benefices?: string[]
  vigilance?: string[]
  devis?: string[]
  fiche?: string
  fiche_question?: string
}
interface Solaire {
  type: 'piste' | 'etude'
  texte?: string
  lien: string
  source?: string
  mention?: string | null
  etude?: {
    date: string; puissance_kwc: number | null; investissement_eur: number | null
    economie_1re_annee_eur: number | null; temps_retour_ans: number | null
    gain_net_25_ans_eur: number | null; autonomie_pct: number | null
  }
}
// v2.3 : un groupe d'actions chiffrées (plan recommandé, ou à prévoir à l'occasion).
interface BlocPlan {
  nb: number
  investissement_eur: Plage
  aides_estimees_eur: Plage
  reste_a_charge_eur: Plage
  economie_annuelle_eur: Fourchette
}
interface AuditResult {
  version_helios: string
  completeness_score: number
  niveau: string
  deperditions: { poste: string; part_pct: number }[]
  // Les clés v1 et v2 coexistent : les audits déjà stockés ne sont jamais recalculés.
  consommation: {
    besoin_kwh_m2_an?: number
    origine_besoin?: string
    surface_m2: number
    conso_chauffage_theorique_kwh_an?: number
    conso_elec_declaree_kwh_an: number | null
    ecart_pct?: number | null
    conso_chauffage_estimee_kwh_an?: number
    origine?: string
    zone_climatique?: string
    conso_chauffage_declaree_kwh_an?: number | null
    message_ratio?: string | null
    base_economies?: 'declaree' | 'estimee'
    releve?: { type: string; unite: string; quantite: number } | null  // v2.7
  }
  priorites: Priorite[]
  synthese: {
    nb_actions: number
    investissement_eur: { bas: number; haut: number }
    aides_estimees_eur: number | Plage
    economie_annuelle_totale_eur: Fourchette | null
    premiere_action: string | null
    // v2.1
    decompte?: string
    reste_a_charge_eur?: Plage
    economie_chauffage_eur?: Fourchette | null
    economie_eau_chaude_eur?: Fourchette | null
    message_sans_isolation?: string | null
    // v2.3
    plan_recommande?: BlocPlan
    a_l_occasion?: BlocPlan
  }
  a_preciser?: { champ: string; libelle: string; hypothese: string }[]
  // v2.1 : conseils sans chiffre et solaire (absents des audits plus anciens)
  gestes?: { cle: string; texte: string; fiche?: string; fiche_question?: string }[]
  conseils_equipements?: { equipement: string; texte: string }[]
  confort_ete?: { conseils: string[]; note_combles: string | null; note_clim?: string | null } | null
  solaire?: Solaire | null
  hypotheses?: { cle: string; valeur: unknown; source: string }[]
  // v2.4
  contrat?: { cle: string; texte: string; fiche?: string; fiche_question?: string }[]
  dpe_attestation?: { texte: string; fiche: string; fiche_question?: string } | null
  renovation_ampleur?: {
    texte: string | null; vigilance: string[]; fossile: string | null; fiche: string; fiche_question?: string
  } | null
  climat?: { chauffage_kg_an: number; eau_chaude_kg_an: number | null; apres_plan_recommande_kg_an: number } | null
  couts?: {
    eau_chaude_eur_an: number | null; hausse_pct_an: number
    chauffage_et_eau_chaude_10_ans_eur: number; economie_10_ans_plan_recommande_eur: number
  } | null
  // v2.6 : la puissance de chauffage et les radiateurs (absents des audits plus anciens)
  puissance?: Puissance | null
  avertissement: string
}
interface Puissance {
  affichage: 'complet' | 'puissance' | null
  texte: string | null; texte_plage: string | null; note_radiateurs: string | null
  radiateurs: { piece: string; verdict: string; texte?: string | null }[]
}

interface AuditRow { id: string; created_at: string; result: AuditResult }

const POSTE_LABEL: Record<string, string> = {
  toiture: 'Toiture / combles', murs: 'Murs', air_ventilation: 'Air / ventilation',
  menuiseries: 'Menuiseries', plancher: 'Plancher bas', ponts_thermiques: 'Ponts thermiques',
}
const eur = (n: number) => n.toLocaleString('fr-FR') + ' €'
const montant = (v: number | Plage) => (typeof v === 'number' ? `~${eur(v)}` : `${eur(v.bas)}–${eur(v.haut)}`)
const ORIGINE: Record<string, string> = {
  dpe: "d'après la lettre DPE", annee_construction: "d'après l'année de construction", defaut: 'valeur par défaut',
}
const HORIZON: Record<string, string> = {
  maintenant: 'Maintenant', prioritaire: 'Prioritaire', a_l_occasion: "À l'occasion",
}
const dec = (n: number) => n.toLocaleString('fr-FR', { maximumFractionDigits: 1 })
// Même seuil que `audit_retour_affichage_max_ans` (api/app/core/config.py) : au-delà, un
// temps de retour ne veut plus rien dire pour le lecteur. Les deux se tiennent à jour ENSEMBLE.
const RETOUR_MAX_ANS = 30
const retour = (n: number) => (n > RETOUR_MAX_ANS ? `> ${RETOUR_MAX_ANS} ans` : `~${dec(n)} ans`)
const aide = (v: number | Plage) => ((typeof v === 'number' ? v === 0 : v.bas === 0 && v.haut === 0) ? 'aucune' : montant(v))
const plage = (p: Plage) => (p.bas === p.haut ? eur(p.bas) : `${eur(p.bas)} à ${eur(p.haut)}`)

function phraseBloc(b: BlocPlan) {
  const aides = b.aides_estimees_eur.bas || b.aides_estimees_eur.haut
    ? `aides ${plage(b.aides_estimees_eur)} selon vos revenus` : "aucune aide MaPrimeRénov'"
  return `coût ${plage(b.investissement_eur)}, ${aides}, reste à charge ${plage(b.reste_a_charge_eur)}, économie ${plage(b.economie_annuelle_eur)} par an`
}
const actions = (n: number) => `${n} action${n > 1 ? 's' : ''}`

/** v2.6 : les phrases de la fiche PAC remplies par le moteur ; l'écran n'ajoute aucun chiffre. */
function BlocPuissance({ b, estimee }: { b: Puissance; estimee: boolean }) {
  const lignes = b.radiateurs.filter((x) => x.texte)
  return (
    <div>
      <h2 className="font-semibold text-lg mb-2">Puissance de chauffage</h2>
      {b.texte && <p className="text-sm text-gray-600">{b.texte}</p>}
      {b.texte_plage && <p className="text-sm text-gray-600 mt-2">{b.texte_plage}</p>}
      {lignes.length > 0 && (
        <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1 mt-2">
          {lignes.map((x) => <li key={x.piece}>{x.texte}</li>)}
        </ul>
      )}
      {b.note_radiateurs && <p className="text-sm text-gray-600 mt-2">{b.note_radiateurs}</p>}
      {/* Pré-audit lot 7 : sans relevé, la puissance repose sur deux estimations. */}
      {estimee && (
        <Link to="/mon-espace#energie" className="mt-2 inline-block text-sm font-semibold text-primary hover:underline">
          Indiquer ma consommation
        </Link>
      )}
    </div>
  )
}

function CartePriorite({ p, numero = true }: { p: Priorite; numero?: boolean }) {
  return (
    <div className="border border-gray-200 rounded-xl p-4">
      <div className="flex items-baseline justify-between gap-2 mb-2">
        <div className="font-medium">
          {numero && <>#{p.rang} </>}{p.label}
          {numero && p.horizon && <span className="ml-2 text-xs text-gray-500">· {HORIZON[p.horizon]}</span>}
        </div>
        {p.temps_retour_ans !== null && (
          <div className="text-xs text-gray-500 shrink-0">
            retour {retour(p.temps_retour_ans)}
            {p.temps_retour_ans > RETOUR_MAX_ANS && <span className="block text-right">non rentable sur l'énergie seule</span>}
          </div>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-600">
        <div>{p.base_cout === 'surcout' ? 'Surcoût' : 'Coût'} : {eur(p.cout_eur.bas)}–{eur(p.cout_eur.haut)}</div>
        <div>Aide : {aide(p.aide_estimee_eur)}</div>
        <div>Reste : {montant(p.reste_a_charge_eur)}</div>
        <div>Éco/an : {eur(p.economie_annuelle_eur.bas)}–{eur(p.economie_annuelle_eur.haut)}</div>
      </div>
      {p.contexte && (
        <div className="text-xs text-gray-500 mt-2">
          {/^[A-ZÀ-Ý]/.test(p.contexte) ? p.contexte : `À faire ${p.contexte}.`}
        </div>
      )}
      {p.libelle_occasion && <div className="text-xs text-gray-500 mt-2">À faire {p.libelle_occasion}.</div>}
      {p.aide_note && <div className="text-xs text-gray-500 mt-1">Aide : {p.aide_note}.</div>}
      <Explications p={p} />
    </div>
  )
}

const point = (l: string[]) => l.join(' · ')

/** Lien vers la question de la fiche dans la FAQ (v2.5 : gestes, contrat, parcours). */
function EnSavoirPlus({ question }: { question?: string }) {
  if (!question) return null
  return (
    <>
      {' '}
      <Link to={`/faq/${faqSlug(question)}`} className="text-primary font-semibold hover:underline whitespace-nowrap">
        En savoir plus
      </Link>
    </>
  )
}

/** v2.4 : le pourquoi en clair, le reste replié — mêmes blocs, même ordre que le PDF
 *  (une action « à l'occasion » ne garde que le pourquoi et ce qu'elle apporte). */
function Explications({ p }: { p: Priorite }) {
  const occasion = p.horizon === 'a_l_occasion'
  const listes: [string, string[] | undefined][] = [
    ['Ce que ça apporte', p.benefices],
    ...(occasion ? [] : ([['À surveiller', p.vigilance], ['Sur le devis', p.devis]] as [string, string[] | undefined][])),
  ]
  const pleines = listes.filter(([, l]) => l && l.length > 0) as [string, string[]][]
  if (!p.pourquoi && !pleines.length) return null
  return (
    <div className="mt-3 space-y-2">
      {p.pourquoi && <p className="text-sm text-gray-700"><strong>Pourquoi :</strong> {p.pourquoi}</p>}
      {pleines.length > 0 && (
        <Depliant titre="En détail" resume={pleines.map(([t]) => t.toLowerCase()).join(', ')}>
          <dl className="text-sm text-gray-700 space-y-2">
            {pleines.map(([t, l]) => (
              <div key={t}><dt className="font-semibold">{t}</dt><dd>{point(l)}</dd></div>
            ))}
          </dl>
          {p.fiche_question && (
            <Link to={`/faq/${faqSlug(p.fiche_question)}`} className="inline-block text-sm text-primary font-semibold hover:underline">
              En savoir plus
            </Link>
          )}
        </Depliant>
      )}
    </div>
  )
}

/** Audits v2.1 : le plan en quatre temps, le confort d'été et les hypothèses par défaut. */
function PlanV21({ r }: { r: AuditResult }) {
  const travaux = r.priorites.filter((p) => p.categorie !== 'production')
  const par = (h: string) => travaux.filter((p) => p.horizon === h)
  const sol = r.solaire
  const defauts = (r.hypotheses ?? []).filter((h) => h.source === 'Fiche Maison' && typeof h.valeur === 'string')
  const Titre = ({ children }: { children: React.ReactNode }) => (
    <h3 className="font-semibold text-primary mt-5 mb-2">{children}</h3>
  )
  return (
    <>
      <div>
        <h2 className="font-semibold text-lg mb-1">Votre plan</h2>
        <p className="text-sm text-gray-600">{r.synthese.decompte}.</p>
        {r.synthese.message_sans_isolation && (
          <p className="text-sm text-gray-700 mt-2">{r.synthese.message_sans_isolation}</p>
        )}

        <Titre>Maintenant</Titre>
        <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
          {(r.gestes ?? []).map((g) => <li key={g.cle}>{g.texte}<EnSavoirPlus question={g.fiche_question} /></li>)}
          {(r.conseils_equipements ?? []).map((c) => <li key={c.equipement}>{c.texte}</li>)}
          {r.dpe_attestation && <li>{r.dpe_attestation.texte}<EnSavoirPlus question={r.dpe_attestation.fiche_question} /></li>}
        </ul>
        {r.contrat && r.contrat.length > 0 && (
          <>
            <p className="text-sm font-semibold text-gray-800 mt-3 mb-1">Votre contrat</p>
            <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
              {r.contrat.map((c) => <li key={c.cle}>{c.texte}<EnSavoirPlus question={c.fiche_question} /></li>)}
            </ul>
          </>
        )}
        <div className="space-y-3 mt-3">{par('maintenant').map((p) => <CartePriorite key={p.rang} p={p} numero={false} />)}</div>

        <Titre>Cette année</Titre>
        {par('prioritaire').length ? (
          <div className="space-y-3">{par('prioritaire').map((p) => <CartePriorite key={p.rang} p={p} numero={false} />)}</div>
        ) : (
          <p className="text-sm text-gray-600">Aucun investissement ne se justifie à court terme : les gestes ci-dessus suffisent pour l'instant.</p>
        )}

        <Titre>À l'occasion de…</Titre>
        {par('a_l_occasion').length ? (
          <div className="space-y-3">{par('a_l_occasion').map((p) => <CartePriorite key={p.rang} p={p} numero={false} />)}</div>
        ) : (
          <p className="text-sm text-gray-600">Rien à prévoir pour l'instant.</p>
        )}

        {(sol || r.renovation_ampleur) && <Titre>Pour aller plus loin</Titre>}
        {sol && (
          <>
            {sol.type === 'piste' ? (
              <p className="text-sm text-gray-700">
                {sol.texte}{' '}
                <Link to={sol.lien} className="text-primary font-semibold hover:underline">Ouvrir le simulateur</Link>
              </p>
            ) : (
              <div className="text-sm text-gray-700 space-y-1">
                {sol.etude?.puissance_kwc != null && <div>Installation étudiée : {dec(sol.etude.puissance_kwc)} kWc</div>}
                {sol.etude?.investissement_eur != null && <div>Investissement : {eur(sol.etude.investissement_eur)}</div>}
                {sol.etude?.economie_1re_annee_eur != null && <div>Économie la première année : {eur(sol.etude.economie_1re_annee_eur)}</div>}
                {sol.etude?.temps_retour_ans != null && <div>Temps de retour : {dec(sol.etude.temps_retour_ans)} ans</div>}
                {sol.etude?.gain_net_25_ans_eur != null && <div>Gain net sur 25 ans : {eur(sol.etude.gain_net_25_ans_eur)}</div>}
                <div className="text-xs text-gray-500">
                  Source : {sol.source}.{sol.mention && <> <strong>{sol.mention}</strong> — <Link to={sol.lien} className="text-primary hover:underline">refaire l'étude</Link>.</>}
                </div>
              </div>
            )}
          </>
        )}
        {r.renovation_ampleur && (
          <div className="text-sm text-gray-700 space-y-1 mt-3">
            {r.renovation_ampleur.texte && <p>{r.renovation_ampleur.texte}<EnSavoirPlus question={r.renovation_ampleur.fiche_question} /></p>}
            {r.renovation_ampleur.fossile && <p className="font-semibold">{r.renovation_ampleur.fossile}</p>}
            {r.renovation_ampleur.vigilance.length > 0 && (
              <p className="text-gray-600"><strong>À surveiller :</strong> {point(r.renovation_ampleur.vigilance)}</p>
            )}
          </div>
        )}
      </div>

      {r.confort_ete && (
        <div>
          <h2 className="font-semibold text-lg mb-2">Confort d'été</h2>
          <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
            {r.confort_ete.conseils.map((c) => <li key={c}>{c}</li>)}
            {r.confort_ete.note_clim && <li>{r.confort_ete.note_clim}</li>}
          </ul>
          {r.confort_ete.note_combles && <p className="text-sm text-gray-700 mt-2">{r.confort_ete.note_combles}</p>}
        </div>
      )}

      <div className="bg-primary/5 border border-primary/20 rounded-2xl p-5">
        <h2 className="font-semibold text-lg mb-2">En résumé</h2>
        {r.synthese.plan_recommande && r.synthese.a_l_occasion ? (
          // v2.3 : le plan recommandé d'abord, ce qui attend une occasion à part — le total de
          // la synthèse additionne les deux, ce qu'on prendrait pour le budget conseillé.
          <>
            <p className="text-sm text-gray-800 font-medium">
              {r.synthese.plan_recommande.nb > 0
                ? <>Le plan recommandé ({actions(r.synthese.plan_recommande.nb)}) : {phraseBloc(r.synthese.plan_recommande)}.</>
                : <>Pas de travaux rentables à court terme : les gestes gratuits sont votre plan pour l'instant.</>}
            </p>
            {r.synthese.a_l_occasion.nb > 0 && (
              <p className="text-sm text-gray-600 mt-2">
                Si vous faites aussi les travaux à prévoir à l'occasion ({actions(r.synthese.a_l_occasion.nb)}) : {phraseBloc(r.synthese.a_l_occasion)}.
              </p>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-700">
            {r.synthese.decompte}.{' '}
            {r.synthese.nb_actions > 0 && r.synthese.reste_a_charge_eur && (
              <>Tous travaux confondus : {eur(r.synthese.investissement_eur.bas)}–{eur(r.synthese.investissement_eur.haut)}, aides {montant(r.synthese.aides_estimees_eur)} selon vos revenus, reste à charge {montant(r.synthese.reste_a_charge_eur)}.</>
            )}
            {r.synthese.economie_chauffage_eur && <> Économie de chauffage : {eur(r.synthese.economie_chauffage_eur.bas)}–{eur(r.synthese.economie_chauffage_eur.haut)}/an.</>}
            {r.synthese.economie_eau_chaude_eur && <> Économie d'eau chaude : {eur(r.synthese.economie_eau_chaude_eur.bas)}–{eur(r.synthese.economie_eau_chaude_eur.haut)}/an.</>}
          </p>
        )}
        <p className="text-sm text-gray-700 mt-2">
          Première étape conseillée : <strong>{r.synthese.premiere_action}</strong>.
        </p>
      </div>

      {r.a_preciser && r.a_preciser.length > 0 && (
        <div>
          <h2 className="font-semibold text-lg mb-2">Pour un pré-audit plus précis</h2>
          <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
            {r.a_preciser.map((a) => <li key={a.champ}>{a.libelle} — {a.hypothese}.</li>)}
          </ul>
          <Link to="/mon-espace" className="inline-block text-sm text-primary font-semibold hover:underline mt-2">
            Compléter ma fiche Maison
          </Link>
        </div>
      )}

      {defauts.length > 0 && (
        <div>
          <h2 className="font-semibold text-lg mb-2">Hypothèses utilisées</h2>
          <ul className="list-disc pl-5 text-xs text-gray-600 space-y-1">
            {defauts.map((h) => <li key={h.cle}>{String(h.valeur)}</li>)}
          </ul>
        </div>
      )}
    </>
  )
}

export default function EspaceAudits() {
  const { authFetch } = useAuth()
  const [score, setScore] = useState<number | null>(null)
  const [audits, setAudits] = useState<AuditRow[]>([])
  const [selected, setSelected] = useState<AuditRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadError, setLoadError] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    setLoadError(false)
    Promise.all([
      // 404 = pas encore de fiche (état normal) ; toute autre erreur = service indisponible.
      authFetch('/api/houses/me').then((r) => (r.ok ? r.json() : r.status === 404 ? null : Promise.reject(new Error(String(r.status))))),
      authFetch('/api/audits').then((r) => (r.ok ? r.json() : r.status === 404 ? [] : Promise.reject(new Error(String(r.status))))),
    ]).then(([house, list]) => {
      setScore(house?.completeness_score ?? null)
      setAudits(list)
      if (list.length > 0) setSelected(list[0])
    }).catch(() => setLoadError(true)).finally(() => setLoading(false))
  }, [authFetch])
  useEffect(load, [load])

  async function generate() {
    setError(null)
    setGenerating(true)
    try {
      const res = await authFetch('/api/audits', { method: 'POST' })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Génération impossible.')
      }
      const created = await res.json()
      const row: AuditRow = { id: created.id, created_at: created.created_at, result: created.result }
      setAudits((prev) => [row, ...prev])
      setSelected(row)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur inconnue')
    } finally {
      setGenerating(false)
    }
  }

  async function downloadPdf(id: string) {
    const res = await authFetch(`/api/audits/${id}/pdf`)
    if (!res.ok) { setError('PDF indisponible.'); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `preaudit-helios-${id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const canGenerate = score !== null && score >= 70
  const r = selected?.result

  return (
    <section className="max-w-[1000px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Mes pré-audits</h1>
      </div>
      <p className="text-gray-600 mb-6">
        Un pré-diagnostic énergétique chiffré, calculé à partir de votre fiche maison. Ordres de grandeur indicatifs.
      </p>

      {loading ? (
        <p className="text-gray-400">Chargement…</p>
      ) : loadError ? (
        <ApiError retry={load} />
      ) : (
        <>
          {/* Bandeau complétude / génération */}
          <div className="bg-gray-50 rounded-2xl p-5 mb-8 flex flex-wrap items-center justify-between gap-4">
            <div className="text-sm">
              Complétude de votre fiche : <strong>{score ?? 0}%</strong>
              {!canGenerate && (
                <span className="text-gray-500">
                  {' '}— il faut au moins <strong>70%</strong> pour générer un pré-audit chiffré.{' '}
                  <Link to="/mon-espace" className="text-primary underline">Compléter ma fiche</Link>
                </span>
              )}
            </div>
            <button
              onClick={generate}
              disabled={!canGenerate || generating}
              className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-40"
            >
              {generating ? 'Calcul en cours…' : 'Générer un pré-audit'}
            </button>
          </div>

          {error && <p className="text-sm text-red-600 mb-6">{error}</p>}

          {audits.length === 0 && !error && (
            <p className="text-gray-400">Aucun pré-audit pour l'instant.</p>
          )}

          {audits.length > 0 && (
            <div className="grid md:grid-cols-[200px_1fr] gap-6">
              {/* Historique */}
              <div className="space-y-1">
                <div className="text-xs font-semibold text-gray-400 mb-1">Historique</div>
                {audits.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => setSelected(a)}
                    className={
                      'block w-full text-left text-xs rounded-lg px-3 py-2 ' +
                      (a.id === selected?.id ? 'bg-primary/10 text-primary font-semibold' : 'hover:bg-gray-100 text-gray-600')
                    }
                  >
                    {new Date(a.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                  </button>
                ))}
              </div>

              {/* Résultat */}
              {r && (
                <div className="space-y-8">
                  <div className="flex justify-end">
                    <button
                      onClick={() => downloadPdf(selected!.id)}
                      className="inline-flex items-center gap-1.5 text-sm rounded-lg border border-primary text-primary px-4 py-2 hover:bg-primary/5"
                    >
                      <Download className="w-4 h-4" /> Télécharger le PDF
                    </button>
                  </div>

                  {/* Déperditions */}
                  <div>
                    <h2 className="font-semibold text-lg mb-3">Où votre logement perd de la chaleur</h2>
                    <div className="space-y-2">
                      {r.deperditions.map((d) => (
                        <div key={d.poste} className="flex items-center gap-3 text-sm">
                          <div className="w-36 shrink-0">{POSTE_LABEL[d.poste] ?? d.poste}</div>
                          <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                            <div className="bg-primary h-full rounded-full" style={{ width: `${d.part_pct}%` }} />
                          </div>
                          <div className="w-12 text-right text-gray-600">{d.part_pct}%</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Consommation */}
                  <div>
                    <h2 className="font-semibold text-lg mb-2">Consommation</h2>
                    {r.consommation.conso_chauffage_estimee_kwh_an !== undefined ? (
                      <p className="text-sm text-gray-600">
                        Consommation de chauffage estimée : <strong>{r.consommation.conso_chauffage_estimee_kwh_an.toLocaleString('fr-FR')} kWh/an</strong>{' '}
                        ({ORIGINE[r.consommation.origine ?? ''] ?? r.consommation.origine}, zone {r.consommation.zone_climatique}).
                        {r.consommation.conso_chauffage_declaree_kwh_an != null && (
                          <> D'après votre {r.consommation.releve ? 'relevé' : 'facture'} : environ {r.consommation.conso_chauffage_declaree_kwh_an.toLocaleString('fr-FR')} kWh/an de chauffage.</>
                        )}
                        {r.consommation.message_ratio && <> {r.consommation.message_ratio}</>}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-600">
                        Besoin de chauffage estimé : <strong>{r.consommation.besoin_kwh_m2_an} kWh/m²/an</strong>{' '}
                        × {r.consommation.surface_m2} m² = <strong>{(r.consommation.conso_chauffage_theorique_kwh_an ?? 0).toLocaleString('fr-FR')} kWh/an</strong>.
                        {r.consommation.conso_elec_declaree_kwh_an && (
                          <> Conso déclarée : {r.consommation.conso_elec_declaree_kwh_an.toLocaleString('fr-FR')} kWh/an.</>
                        )}
                      </p>
                    )}
                    {r.couts && (
                      <p className="text-sm text-gray-600 mt-2">
                        Sur 10 ans, à +{dec(r.couts.hausse_pct_an)} %/an, {r.couts.eau_chaude_eur_an ? 'votre chauffage et votre eau chaude vous coûteraient' : 'votre chauffage vous coûterait'} environ {eur(r.couts.chauffage_et_eau_chaude_10_ans_eur)}
                        {r.couts.economie_10_ans_plan_recommande_eur > 0 && <> ; le plan recommandé en économiserait environ {eur(r.couts.economie_10_ans_plan_recommande_eur)}</>}.
                      </p>
                    )}
                    {r.climat && (
                      <p className="text-sm text-gray-600 mt-1">
                        Émissions de CO₂ : environ {(r.climat.chauffage_kg_an + (r.climat.eau_chaude_kg_an ?? 0)).toLocaleString('fr-FR')} kg/an aujourd'hui, {r.climat.apres_plan_recommande_kg_an.toLocaleString('fr-FR')} kg/an après le plan recommandé.
                      </p>
                    )}
                  </div>

                  {r.puissance?.affichage && <BlocPuissance b={r.puissance} estimee={r.consommation.base_economies === 'estimee'} />}

                  {r.gestes ? <PlanV21 r={r} /> : (
                  <>
                  {/* Priorités */}
                  <div>
                    <h2 className="font-semibold text-lg mb-3">Vos priorités de travaux</h2>
                    <div className="space-y-3">
                      {r.priorites.map((p) => <CartePriorite key={p.rang} p={p} />)}
                    </div>
                  </div>

                  {/* Synthèse */}
                  <div className="bg-primary/5 border border-primary/20 rounded-2xl p-5">
                    <h2 className="font-semibold text-lg mb-2">Synthèse</h2>
                    <p className="text-sm text-gray-700">
                      <strong>{r.synthese.nb_actions} actions</strong> recommandées. Investissement estimé :{' '}
                      {eur(r.synthese.investissement_eur.bas)}–{eur(r.synthese.investissement_eur.haut)}, aides {montant(r.synthese.aides_estimees_eur)}.
                      {r.synthese.economie_annuelle_totale_eur && (
                        <> Économie annuelle potentielle : <strong>{eur(r.synthese.economie_annuelle_totale_eur.bas)}–{eur(r.synthese.economie_annuelle_totale_eur.haut)}</strong>.</>
                      )}
                    </p>
                    {r.synthese.premiere_action && (
                      <p className="text-sm text-gray-700 mt-2">
                        Première étape conseillée : <strong>{r.synthese.premiere_action}</strong>.
                      </p>
                    )}
                  </div>

                  </>
                  )}

                  <p className="text-xs text-gray-400">{r.avertissement}</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  )
}
