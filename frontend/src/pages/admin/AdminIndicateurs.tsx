import { useState } from 'react'
import { AlertTriangle, PhoneMissed } from 'lucide-react'
import { Attente, Erreur, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
import { dateCourte } from '../../components/mer/libelles'
import { nomDuMois } from '../../components/mer/Releve'
import { useTitle } from '../../hooks/useTitle'

/** Qualité du réseau (mises en relation, lot 5) : indicateurs du mois et cumul, chacun avec sa
 *  source, et les écarts entre foyers et partenaires. Interne : jamais publié, jamais un classement. */
interface Indicateur {
  cle: string; libelle: string; valeur: number | null; unite: string; source: string
  numerateur: number | null; denominateur: number | null
}
interface Ecart {
  lead_id: string; partenaire: string; demo: boolean; metier: string | null; code_postal: string | null
  transmis_le: string; statut_partenaire: string; contact_foyer: string | null; sans_contact_signale: boolean
  ecarts: { sujet: string; foyer: string; partenaire: string }[]; prix_ht: number | null; facturable: boolean
  mois: string; releve_clos: boolean
}

const SOURCE_STYLE: Record<string, string> = {
  'calculé': 'border-bord bg-sable text-dark/70',
  'déclaré partenaire': 'border-sky/40 bg-sky/10 text-sky',
  'déclaré foyer': 'border-leaf/40 bg-leaf/10 text-leaf',
}

function valeur(i: Indicateur): string {
  if (i.valeur == null) return '—'
  const v = i.valeur.toLocaleString('fr-FR')
  if (i.unite === '€') return i.valeur.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })
  return i.unite === '%' ? `${v} %` : i.unite ? `${v} ${i.unite}` : v
}

function Colonne({ titre, liste }: { titre: string; liste: Indicateur[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-bord bg-white">
      <h2 className="border-b border-bord bg-sable px-3 py-2 text-sm font-semibold text-ink">{titre}</h2>
      <ul className="divide-y divide-bord text-sm">
        {liste.map((i) => (
          <li key={i.cle} className="flex flex-wrap items-center gap-x-2 gap-y-1 px-3 py-2">
            <span className="min-w-0 flex-1 text-dark/80">{i.libelle}</span>
            <span className={'rounded-full border px-2 py-0.5 text-xs ' + SOURCE_STYLE[i.source]}>{i.source}</span>
            <span className="w-24 text-right font-semibold text-ink">{valeur(i)}</span>
            {i.denominateur != null && <span className="w-full text-right text-xs text-dark/50">{i.numerateur} sur {i.denominateur}</span>}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function AdminIndicateurs() {
  useTitle('Back-office — Indicateurs')
  const [mois, setMois] = useState(new Date().toLocaleDateString('sv-SE').slice(0, 7))
  const [demo, setDemo] = useState(false)
  const ind = useAdminData<{ du_mois: Indicateur[]; cumul: Indicateur[] }>(`/api/admin/mer/indicateurs?mois=${mois}&demo=${demo}`)
  const ecarts = useAdminData<Ecart[]>(`/api/admin/mer/ecarts?demo=${demo}`)

  return (
    <>
      <TitrePage titre="Indicateurs">
        La qualité du réseau de mises en relation, par mois de transmission et en cumul. Chaque chiffre dit d'où il vient :
        déclaré par le partenaire, par le foyer, ou calculé. Usage interne : aucun classement public n'en est tiré.
      </TitrePage>

      <div className="mt-6 flex flex-wrap items-center gap-4 text-sm text-dark/70">
        <label className="flex items-center gap-2">Mois
          <input type="month" value={mois} onChange={(e) => setMois(e.target.value)}
            className="rounded-lg border border-bord bg-white px-3 py-1.5 text-ink" />
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={demo} onChange={(e) => setDemo(e.target.checked)} />
          Inclure les partenaires de démonstration
        </label>
      </div>

      {ind.error && <Erreur>{ind.error}</Erreur>}
      {!ind.data && !ind.error && <Attente />}
      {ind.data && (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <Colonne titre={nomDuMois(mois)} liste={ind.data.du_mois} />
          <Colonne titre="Cumul" liste={ind.data.cumul} />
        </div>
      )}

      <section className="mt-8">
        <h2 className="mb-1 text-xl text-ink">Écarts et demandes sans contact</h2>
        <p className="mb-3 text-sm text-dark/70">
          Quand le foyer et le partenaire se contredisent, ou quand le foyer dit ne pas avoir été appelé. Le prix n'est jamais
          annulé tout seul : un avoir se décide ici, tant que le relevé du mois n'est pas clos.
        </p>
        {ecarts.data?.length === 0 && <p className="text-sm text-dark/60">Aucun écart.</p>}
        <div className="space-y-2">
          {(ecarts.data ?? []).map((e) => (
            <div key={e.lead_id} className="rounded-xl border border-bord bg-white p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-ink">{e.partenaire}</span>
                {e.demo && <span className="text-xs text-dark/55">(Démo)</span>}
                <span className="text-dark/60">· {e.metier} · {e.code_postal} · transmise le {dateCourte(e.transmis_le)}</span>
                <span className="ml-auto text-dark/60">
                  {e.prix_ht != null && `${e.prix_ht} € HT · `}{e.facturable ? 'facturable' : 'non facturable'}
                  {' · relevé '}{e.releve_clos ? 'clos' : 'non clos'}
                </span>
              </div>
              {e.sans_contact_signale && (
                <p className="mt-1 flex items-center gap-1.5 text-terra"><PhoneMissed className="h-4 w-4" /> Le foyer signale ne pas avoir été contacté.</p>
              )}
              {e.ecarts.map((x, i) => (
                <p key={i} className="mt-1 flex items-center gap-1.5 text-ink">
                  <AlertTriangle className="h-4 w-4 text-primary" />
                  {x.sujet === 'contact' ? 'Contact' : 'Signature'} : le foyer dit « {x.foyer} », le partenaire « {x.partenaire} ».
                </p>
              ))}
            </div>
          ))}
        </div>
      </section>
    </>
  )
}
