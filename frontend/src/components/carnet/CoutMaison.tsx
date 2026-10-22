import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Receipt } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { messageErreur } from './Formulaires'
import { useMaj } from './commun'
import { dateFr } from './libelles'

/**
 * « Ce que coûte ma maison » (carnet, lot 10), dans « Ma maison ».
 *
 * Tout vient du serveur (`services/cout_maison.py`) : l'écran n'additionne ni ne recalcule
 * rien. Chaque montant dit d'où il vient ; un poste vide s'écrit « Non renseigné », jamais
 * 0 ; et « Ce que vos projets changeraient » recopie le pré-audit et les études, datés.
 * Ni valeur du bien, ni prêt : Hélios n'est pas un outil bancaire.
 */

type Poste = {
  code: string; montant_eur: number | null; statut: string | null; libelle?: string | null
  conso_kwh_an?: number; prix_eur_kwh?: number; prix_date?: string; kva?: number; kva_suppose?: boolean
  nb_entrees?: number; depuis?: string; raison?: string | null; type_energie?: string | null
}
type Action = {
  action: string; label: string; horizon: string; cout_eur: { bas: number; haut: number }
  economie_annuelle_eur: { bas: number; haut: number; central?: number } | null; temps_retour_ans: number | null
}
type Etude = {
  id: string; date: string; nom: string | null; investissement_eur: number | null
  economie_1re_annee_eur: number | null; temps_retour_ans: number | null; puissance_kwc: number | null
}
type Cout = {
  postes: Poste[]; total_an_eur: number | null; total_mois_eur: number | null; postes_manquants: string[]
  effet_travaux: { audit: { id: string; date: string; actions: Action[] } | null; etudes: Etude[] }
}
type Charges = Record<string, number | string | null>

const NOMS: Record<string, string> = {
  electricite: 'Électricité', autre_energie: 'Autre énergie', entretien: 'Entretien et réparations',
  assurance: 'Assurance habitation', taxe_fonciere: 'Taxe foncière', charges_copro: 'Charges de copropriété',
  eau: 'Eau', autre: 'Autre',
}
// Une couleur par poste, prise dans les jetons de la charte.
const COULEURS: Record<string, string> = {
  electricite: 'bg-primary', autre_energie: 'bg-terra', entretien: 'bg-sun', assurance: 'bg-sky',
  taxe_fonciere: 'bg-ink', charges_copro: 'bg-ink/60', eau: 'bg-sky/60', autre: 'bg-leaf',
}
const CHAMPS_CHARGES: [string, string][] = [
  ['assurance', 'assurance_eur_an'], ['taxe_fonciere', 'taxe_fonciere_eur_an'],
  ['charges_copro', 'charges_copro_eur_an'], ['eau', 'eau_eur_an'], ['autre', 'autre_eur_an'],
]
const HORIZONS: Record<string, string> = { maintenant: 'maintenant', prioritaire: 'prioritaire', a_l_occasion: "à l'occasion" }
// Même seuil que `audit_retour_affichage_max_ans` (api/app/core/config.py) et `EspaceAudits.tsx`.
const RETOUR_MAX_ANS = 30

const euros = (n: number) => `${Math.round(n).toLocaleString('fr-FR')} €`
const prix = (n: number) => `${n.toLocaleString('fr-FR', { minimumFractionDigits: 4 })} €/kWh`
const retour = (n: number | null) => (n === null ? null : n > RETOUR_MAX_ANS ? `> ${RETOUR_MAX_ANS} ans` : `~${Math.round(n)} ans`)

/** D'où vient le montant, en une ligne. */
function Origine({ p }: { p: Poste }) {
  if (p.code === 'electricite' && p.montant_eur !== null) {
    return <>Calculé : {p.conso_kwh_an?.toLocaleString('fr-FR')} kWh × {prix(p.prix_eur_kwh ?? 0)}, prix supposé (tarif
      réglementé au {dateFr(p.prix_date)}{p.kva_suppose ? `, ${p.kva} kVA supposés` : `, ${p.kva} kVA`}), hors abonnement.</>
  }
  if (p.code === 'electricite') return <>Indiquez votre consommation dans <Link to="/mon-espace" className="text-primary hover:underline">votre fiche</Link>.</>
  if (p.code === 'autre_energie') {
    return p.raison === 'unite_inconnue'
      ? <>Votre fiche indique {p.type_energie} sans unité : pas de montant, plutôt qu'un montant faux.</>
      : null
  }
  if (p.code === 'entretien') {
    return p.montant_eur !== null
      ? <>Calculé : {p.nb_entrees} dépense{(p.nb_entrees ?? 0) > 1 ? 's' : ''} notée{(p.nb_entrees ?? 0) > 1 ? 's' : ''} au journal depuis le {dateFr(p.depuis)}.</>
      : <>Aucune dépense notée au journal depuis le {dateFr(p.depuis)}.</>
  }
  return p.montant_eur !== null ? <>Déclaré par vous.</> : null
}

function FormCharges({ applicables, onFini }: { applicables: string[]; onFini: () => void }) {
  const { authFetch } = useAuth()
  const [c, setC] = useState<Charges | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  useEffect(() => {
    authFetch('/api/houses/me/charges').then((r) => (r.ok ? r.json() : null)).then(setC)
  }, [authFetch])
  if (!c) return null

  async function envoyer(e: React.FormEvent) {
    e.preventDefault()
    // Le PUT remplace l'ensemble : on renvoie aussi ce que le formulaire ne montre pas.
    const res = await authFetch('/api/houses/me/charges', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(c),
    })
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    onFini()
  }
  const champ = 'mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm'
  return (
    <form onSubmit={envoyer} className="space-y-3 rounded-lg border border-primary/30 bg-cream/60 p-3">
      <p className="text-sm font-semibold text-ink">Mes charges, en euros par an</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {CHAMPS_CHARGES.filter(([code]) => applicables.includes(code)).map(([code, cle]) => (
          <label key={cle} className="text-sm">{NOMS[code]}
            <input type="number" min={0} step="any" value={c[cle] ?? ''} className={champ}
              onChange={(e) => setC({ ...c, [cle]: e.target.value === '' ? null : Number(e.target.value) })} />
          </label>
        ))}
        <label className="text-sm">Autre : de quoi s'agit-il ?
          <input maxLength={80} value={(c.autre_libelle as string) ?? ''} className={champ}
            onChange={(e) => setC({ ...c, autre_libelle: e.target.value || null })} />
        </label>
      </div>
      <p className="text-xs text-dark/60">Tout est facultatif. Un champ vide reste « Non renseigné ».</p>
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90">Enregistrer</button>
        <button type="button" onClick={onFini}
          className="rounded-lg border border-bord px-4 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">Annuler</button>
      </div>
    </form>
  )
}

export default function CoutMaison() {
  const { authFetch } = useAuth()
  const [r, setR] = useState<Cout | null>(null)
  const [form, setForm] = useState(false)

  const charger = useCallback(() => {
    authFetch('/api/houses/me/cout').then((res) => (res.ok ? res.json() : null)).then(setR)
  }, [authFetch])
  useEffect(charger, [charger])
  useMaj(charger)  // une dépense notée au journal change l'entretien

  if (!r) return null
  const renseignes = r.postes.filter((p) => p.montant_eur !== null)
  const total = r.total_an_eur ?? 0
  const { audit, etudes } = r.effet_travaux

  return (
    <section id="cout-maison" className="scroll-mt-20 rounded-xl border border-ink/10 bg-white p-4">
      <h2 className="mb-3 flex items-center gap-2 font-display text-xl text-ink">
        <Receipt className="h-5 w-5 text-primary" /> Ce que coûte ma maison
      </h2>

      {r.total_an_eur === null ? (
        <p className="text-sm text-dark/70">Rien n'est encore renseigné : complétez votre consommation et vos charges.</p>
      ) : (
        <>
          <p className="flex flex-wrap items-baseline gap-x-3">
            <span className="font-display text-3xl text-ink">{euros(r.total_an_eur)}</span>
            <span className="text-sm text-dark/70">par an, soit {euros(r.total_mois_eur ?? 0)} par mois</span>
          </p>
          <p className="mb-2 text-xs text-dark/60">
            Sur {renseignes.length} poste{renseignes.length > 1 ? 's' : ''} renseigné{renseignes.length > 1 ? 's' : ''}
            {r.postes_manquants.length > 0 && ` ; ${r.postes_manquants.length} ne le sont pas encore et n'y comptent pas`}.
          </p>
          {/* Barre de répartition : des largeurs en CSS, aucune bibliothèque. */}
          <div className="mb-3 flex h-3 overflow-hidden rounded-full bg-bord" role="img"
            aria-label={renseignes.map((p) => `${NOMS[p.code]} ${euros(p.montant_eur ?? 0)}`).join(', ')}>
            {renseignes.map((p) => (
              <div key={p.code} className={COULEURS[p.code] ?? 'bg-dark/40'} style={{ width: `${(100 * (p.montant_eur ?? 0)) / total}%` }} />
            ))}
          </div>
        </>
      )}

      <ul className="divide-y divide-bord">
        {r.postes.map((p) => (
          <li key={p.code} className="flex items-start gap-3 py-2">
            <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${p.montant_eur !== null ? COULEURS[p.code] : 'bg-bord'}`} />
            <span className="min-w-0 flex-1 text-sm">
              <span className="block text-ink">{NOMS[p.code]}{p.code === 'autre' && p.libelle ? ` — ${p.libelle}` : ''}</span>
              <span className="block text-xs text-dark/60"><Origine p={p} /></span>
            </span>
            <span className={'shrink-0 text-sm ' + (p.montant_eur !== null ? 'font-semibold text-ink' : 'text-dark/50')}>
              {p.montant_eur !== null ? `${euros(p.montant_eur)}/an` : 'Non renseigné'}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-3">
        {form
          ? <FormCharges applicables={r.postes.map((p) => p.code)} onFini={() => { setForm(false); charger() }} />
          : <button onClick={() => setForm(true)} className="text-sm font-semibold text-primary hover:underline">Compléter mes charges</button>}
      </div>

      <div className="mt-5 border-t border-bord pt-4">
        <h3 className="mb-2 font-display text-lg text-ink">Ce que vos projets changeraient</h3>
        {!audit && etudes.length === 0 ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-dark/70">Aucun calcul encore : un pré-audit chiffre ce que chaque action changerait.</p>
            <Link to="/espace/audits" className="rounded-lg border border-primary px-3.5 py-2 text-sm font-semibold text-primary hover:bg-primary/5">
              Faire mon pré-audit
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {audit && audit.actions.length > 0 && (
              <div>
                <p className="mb-1 text-xs text-dark/60">
                  D'après votre <Link to="/espace/audits" className="text-primary hover:underline">pré-audit du {dateFr(audit.date)}</Link>, tel qu'il a été calculé.
                </p>
                <ul className="divide-y divide-bord rounded-lg border border-bord">
                  {audit.actions.map((a) => (
                    <li key={a.action} className="px-3 py-2 text-sm">
                      <span className="block text-ink">{a.label} <span className="text-xs text-dark/50">· {HORIZONS[a.horizon] ?? a.horizon}</span></span>
                      <span className="block text-xs text-dark/60">
                        {euros(a.cout_eur.bas)} à {euros(a.cout_eur.haut)}
                        {a.economie_annuelle_eur && ` · économie ${euros(a.economie_annuelle_eur.central ?? a.economie_annuelle_eur.bas)}/an`}
                        {retour(a.temps_retour_ans) && ` · retour ${retour(a.temps_retour_ans)}`}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {etudes.length > 0 && (
              <div>
                <p className="mb-1 text-xs text-dark/60">Vos études du <Link to="/simulateur-solaire" className="text-primary hover:underline">simulateur</Link>, telles qu'elles ont été calculées.</p>
                <ul className="divide-y divide-bord rounded-lg border border-bord">
                  {etudes.map((e) => (
                    <li key={e.id} className="px-3 py-2 text-sm">
                      <span className="block text-ink">{e.nom || 'Étude'} <span className="text-xs text-dark/50">· {dateFr(e.date)}</span></span>
                      <span className="block text-xs text-dark/60">
                        {e.investissement_eur !== null && `${euros(e.investissement_eur)}`}
                        {e.economie_1re_annee_eur !== null && ` · économie ${euros(e.economie_1re_annee_eur)} la 1re année`}
                        {retour(e.temps_retour_ans) && ` · retour ${retour(e.temps_retour_ans)}`}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
