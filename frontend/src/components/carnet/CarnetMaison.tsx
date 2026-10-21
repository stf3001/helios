import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Pencil, Trash2, Archive, RotateCcw, ShieldCheck, Wrench } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import ApiError from '../ApiError'
import Depliant from '../Depliant'
import { faqSlug } from '../../lib/faqSlug'
import MesPieces from './MesPieces'
import type { Draft } from '../fiche/types'
import {
  type Chantier, type Doc, type Equipement, type Garantie, FormChantier, FormEquipement, messageErreur,
} from './Formulaires'
import {
  CATEGORIES, FICHE_GARANTIES, dateFr, libelleType, phraseSuggestion,
} from './libelles'

/**
 * Carnet de maison, lot 1 : « Mes équipements » et « Travaux et garanties ».
 *
 * Tout ce que le foyer saisit est DÉCLARÉ ; l'âge et les fins de garantie sont CALCULÉS
 * côté serveur, et une année sans date donne une date SUPPOSÉE — l'écran le dit à chaque
 * fois. Aucune explication juridique ici : « En savoir plus » renvoie à la fiche
 * `kb/garanties_travaux.md`. La fiche Maison n'est jamais modifiée depuis ce carnet.
 */

type Suggestion = {
  origine_fiche: string; categorie: string; type: string | null
  annee_pose: number | null; valeur_fiche: string | null
}
type GarantieMaison = Garantie & { provenance: 'travaux' | 'equipement'; donnees: string; mention: string | null }
type Fiche = Record<string, unknown>

// Ce que l'API accepte en écriture : le reste (âge, identifiants, dates système) est calculé.
const CHAMPS_EQUIPEMENT = [
  'categorie', 'type', 'marque', 'modele', 'numero_serie', 'puissance', 'unite', 'date_pose', 'annee_pose',
  'installateur', 'garantie_fabricant_fin', 'contrat_entretien', 'contrat_prestataire', 'travaux_id', 'note',
]
const CHAMPS_CHANTIER = [
  'nature', 'entreprise', 'date_reception', 'montant_ttc', 'facture_document_id',
  'attestation_assurance_document_id', 'note',
]

const choisir = (d: Draft, champs: string[]) =>
  Object.fromEntries(champs.filter((k) => k in d).map((k) => [k, d[k] === '' ? null : d[k]]))

const STATUT: Record<string, { label: string; classe: string }> = {
  en_cours: { label: 'en cours', classe: 'bg-leaf/10 text-leaf' },
  bientot: { label: 'se termine bientôt', classe: 'bg-terra/10 text-terra' },
  expiree: { label: 'terminée', classe: 'bg-cream text-dark/50' },
}

function Pastille({ statut }: { statut: string }) {
  const s = STATUT[statut] ?? STATUT.expiree
  return <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${s.classe}`}>{s.label}</span>
}

function BoutonAjout({ onClick, children }: { onClick: () => void; children: string }) {
  return (
    <button onClick={onClick}
      className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90">
      <Plus className="h-4 w-4" /> {children}
    </button>
  )
}

/** « posé en 2014 · 12 ans » — « environ » quand la date part d'une année seule. */
function lignePose(e: Equipement): string | null {
  if (!e.date_pose_retenue) return null
  const pose = e.date_pose ? `posé le ${dateFr(e.date_pose)}` : `posé en ${e.annee_pose}`
  if (e.age_ans === null) return pose
  const age = e.age_ans === 0 ? "moins d'un an" : `${e.age_ans} an${e.age_ans > 1 ? 's' : ''}`
  return `${pose} · ${e.age_statut === 'suppose' ? 'environ ' : ''}${age}`
}

/** L'année que la fiche Maison indique pour ce champ, si elle diffère de celle de l'équipement. */
function ecartFiche(e: Equipement, fiche: Fiche | null): number | null {
  if (!fiche || !e.origine_fiche || !e.date_pose_retenue) return null
  const annee = fiche[`${e.origine_fiche}_annee`]
  if (typeof annee !== 'number') return null
  return Number(e.date_pose_retenue.slice(0, 4)) === annee ? null : annee
}

function CarteEquipement({ e, fiche, onModifier, onService, onSupprimer }: {
  e: Equipement; fiche: Fiche | null
  onModifier: () => void; onService: () => void; onSupprimer: () => void
}) {
  const nom = [e.marque, e.modele].filter(Boolean).join(' ')
  const pose = lignePose(e)
  const ecart = ecartFiche(e, fiche)
  return (
    <li className="rounded-lg border border-bord bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-ink">{libelleType(e.categorie, e.type)}</p>
          {nom && <p className="text-sm text-dark/70">{nom}</p>}
          {pose && <p className="text-xs text-dark/60">{pose}</p>}
          {e.garantie_fabricant_fin && (
            <p className="text-xs text-dark/60">Garantie fabricant jusqu'au {dateFr(e.garantie_fabricant_fin)}</p>
          )}
          {ecart !== null && <p className="mt-1 text-xs text-terra">Votre fiche indique {ecart}.</p>}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button onClick={onModifier} title="Modifier" aria-label="Modifier"
            className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-primary"><Pencil className="h-4 w-4" /></button>
          <button onClick={onService} title={e.en_service ? 'Mettre hors service' : 'Remettre en service'}
            aria-label={e.en_service ? 'Mettre hors service' : 'Remettre en service'}
            className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-primary">
            {e.en_service ? <Archive className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />}
          </button>
          <button onClick={onSupprimer} title="Supprimer" aria-label="Supprimer"
            className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-terra"><Trash2 className="h-4 w-4" /></button>
        </div>
      </div>
    </li>
  )
}

export default function CarnetMaison() {
  const { authFetch } = useAuth()
  const [equipements, setEquipements] = useState<Equipement[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [chantiers, setChantiers] = useState<Chantier[]>([])
  const [garanties, setGaranties] = useState<GarantieMaison[]>([])
  const [documents, setDocuments] = useState<Doc[]>([])
  const [fiche, setFiche] = useState<Fiche | null>(null)
  const [erreur, setErreur] = useState(false)
  // Un seul formulaire ouvert à la fois : `id` absent = création.
  const [formEq, setFormEq] = useState<Draft | null>(null)
  const [formCh, setFormCh] = useState<Draft | null>(null)

  const charger = useCallback(() => {
    setErreur(false)
    const json = (url: string) => authFetch(url).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
    Promise.all([
      json('/api/houses/me/equipements'), json('/api/houses/me/equipements/suggestions'),
      json('/api/houses/me/travaux'), json('/api/houses/me/garanties'), json('/api/houses/me/documents'),
      authFetch('/api/houses/me').then((r) => (r.ok ? r.json() : null)),
    ]).then(([eq, sg, ch, ga, docs, f]) => {
      setEquipements(eq); setSuggestions(sg); setChantiers(ch); setGaranties(ga); setDocuments(docs); setFiche(f)
    }).catch(() => setErreur(true))
  }, [authFetch])
  useEffect(charger, [charger])

  async function ecrire(url: string, method: string, corps?: object): Promise<string | null> {
    const res = await authFetch(url, {
      method, headers: { 'Content-Type': 'application/json' }, body: corps ? JSON.stringify(corps) : undefined,
    })
    if (!res.ok) return messageErreur(res)
    charger()
    return null
  }

  async function enregistrerEquipement(d: Draft) {
    const id = d.id as string | undefined
    const corps = choisir(d, CHAMPS_EQUIPEMENT)
    if (!id && d.origine_fiche) corps.origine_fiche = d.origine_fiche
    const err = await ecrire(id ? `/api/houses/me/equipements/${id}` : '/api/houses/me/equipements', id ? 'PATCH' : 'POST', corps)
    if (!err) setFormEq(null)
    return err
  }

  async function enregistrerChantier(d: Draft) {
    const id = d.id as string | undefined
    const err = await ecrire(id ? `/api/houses/me/travaux/${id}` : '/api/houses/me/travaux', id ? 'PATCH' : 'POST',
      choisir(d, CHAMPS_CHANTIER))
    if (!err) setFormCh(null)
    return err
  }

  if (erreur) return <ApiError retry={charger} />

  const enService = equipements.filter((e) => e.en_service)
  const anciens = equipements.filter((e) => !e.en_service)
  const ouvertes = garanties.filter((g) => g.statut !== 'expiree')
  const parCategorie = CATEGORIES.map((c) => ({ ...c, items: enService.filter((e) => e.categorie === c.value) }))
    .filter((c) => c.items.length)

  const carte = (e: Equipement) => (
    <CarteEquipement key={e.id} e={e} fiche={fiche}
      onModifier={() => { setFormCh(null); setFormEq({ ...e }) }}
      onService={() => ecrire(`/api/houses/me/equipements/${e.id}`, 'PATCH', { en_service: !e.en_service })}
      onSupprimer={() => {
        if (confirm(`Supprimer « ${libelleType(e.categorie, e.type)} » du carnet ? Pour garder son historique, mettez-le plutôt hors service.`))
          ecrire(`/api/houses/me/equipements/${e.id}`, 'DELETE')
      }} />
  )

  return (
    <div className="space-y-4">
      {/* — Mes équipements — */}
      <section className="rounded-xl border border-ink/10 bg-white p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 font-display text-xl text-ink">
            <Wrench className="h-5 w-5 text-primary" /> Mes équipements
          </h2>
          {enService.length > 0 && !formEq && (
            <BoutonAjout onClick={() => { setFormCh(null); setFormEq({ categorie: 'chauffage' }) }}>Ajouter</BoutonAjout>
          )}
        </div>

        {suggestions.length > 0 && !formEq && (
          <ul className="mb-3 space-y-2">
            {suggestions.map((s) => (
              <li key={s.origine_fiche}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-primary/30 bg-cream px-3 py-2">
                <span className="text-sm text-dark/80">
                  {phraseSuggestion(s.origine_fiche, s.valeur_fiche, s.annee_pose)} L'ajouter à vos équipements ?
                </span>
                <button onClick={() => { setFormCh(null); setFormEq({
                  categorie: s.categorie, type: s.type, annee_pose: s.annee_pose, origine_fiche: s.origine_fiche,
                }) }} className="shrink-0 text-sm font-semibold text-primary hover:underline">
                  Ajouter
                </button>
              </li>
            ))}
          </ul>
        )}

        {formEq && (
          <div className="mb-3">
            <FormEquipement key={String(formEq.id ?? formEq.origine_fiche ?? 'nouveau')} initial={formEq}
              chantiers={chantiers} enregistrer={enregistrerEquipement} onAnnuler={() => setFormEq(null)} />
          </div>
        )}

        {enService.length === 0 && !formEq ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-dark/70">
              Chaudière, ballon, panneaux… Notez vos appareils une fois : Helios saura leur âge et leurs garanties.
            </p>
            <BoutonAjout onClick={() => setFormEq({ categorie: 'chauffage' })}>Ajouter un équipement</BoutonAjout>
          </div>
        ) : (
          <div className="space-y-4">
            {parCategorie.map((c) => (
              <div key={c.value}>
                <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-dark/50">{c.label}</h3>
                <ul className="grid gap-2 sm:grid-cols-2">{c.items.map(carte)}</ul>
              </div>
            ))}
          </div>
        )}

        {anciens.length > 0 && (
          <div className="mt-4">
            <Depliant titre="Anciens équipements" resume={`${anciens.length}`}>
              <ul className="grid gap-2 sm:grid-cols-2">{anciens.map(carte)}</ul>
            </Depliant>
          </div>
        )}
      </section>

      {/* — Mes pièces (lot 2) : sous les équipements, qui alimentent ses émetteurs — */}
      <MesPieces equipements={enService} />

      {/* — Travaux et garanties — */}
      <section className="rounded-xl border border-ink/10 bg-white p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 font-display text-xl text-ink">
            <ShieldCheck className="h-5 w-5 text-primary" /> Travaux et garanties
          </h2>
          {chantiers.length > 0 && !formCh && (
            <BoutonAjout onClick={() => { setFormEq(null); setFormCh({}) }}>Ajouter</BoutonAjout>
          )}
        </div>

        {formCh && (
          <div className="mb-3">
            <FormChantier key={String(formCh.id ?? 'nouveau')} initial={formCh} documents={documents}
              enregistrer={enregistrerChantier} onAnnuler={() => setFormCh(null)} />
          </div>
        )}

        {ouvertes.length > 0 && (
          <div className="mb-4">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-dark/50">Garanties en cours</h3>
            <ul className="divide-y divide-bord rounded-lg border border-bord">
              {ouvertes.map((g) => (
                <li key={`${g.provenance}-${g.code}-${g.libelle}`} className="flex items-start justify-between gap-2 px-3 py-2">
                  <span className="min-w-0 text-sm">
                    <span className="block text-ink">{g.libelle}</span>
                    <span className="block text-xs text-dark/60">
                      jusqu'au {dateFr(g.fin)} · {g.donnees === 'declare' ? 'date que vous avez indiquée' : 'calculée depuis la réception'}
                    </span>
                  </span>
                  <Pastille statut={g.statut} />
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-dark/60">
              Garanties de chantier : à vérifier sur votre contrat et l'attestation d'assurance de l'entreprise.{' '}
              <Link to={`/faq/${faqSlug(FICHE_GARANTIES)}`} className="font-semibold text-primary hover:underline">
                En savoir plus
              </Link>
            </p>
          </div>
        )}

        {chantiers.length === 0 && !formCh ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-dark/70">
              Des travaux réceptionnés ? Notez la date de réception : Helios calcule leurs garanties.
            </p>
            <BoutonAjout onClick={() => setFormCh({})}>Ajouter un chantier</BoutonAjout>
          </div>
        ) : (
          <ul className="space-y-2">
            {chantiers.map((c) => (
              <li key={c.id} className="rounded-lg border border-bord p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-ink">{c.nature}</p>
                    <p className="text-xs text-dark/60">
                      {[c.entreprise, c.date_reception ? `réceptionné le ${dateFr(c.date_reception)}` : 'date de réception à indiquer']
                        .filter(Boolean).join(' · ')}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <button onClick={() => { setFormEq(null); setFormCh({ id: c.id, ...choisir(c as unknown as Draft, CHAMPS_CHANTIER) }) }} title="Modifier" aria-label="Modifier"
                      className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-primary"><Pencil className="h-4 w-4" /></button>
                    <button onClick={() => { if (confirm(`Supprimer le chantier « ${c.nature} » ?`)) ecrire(`/api/houses/me/travaux/${c.id}`, 'DELETE') }}
                      title="Supprimer" aria-label="Supprimer"
                      className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-terra"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </div>
                {c.garanties.length > 0 && (
                  <ul className="mt-2 grid gap-1.5 sm:grid-cols-3">
                    {c.garanties.map((g) => (
                      <li key={g.code} className="flex flex-col gap-1 rounded-md bg-sable/60 px-2.5 py-1.5 text-xs">
                        <span className="font-semibold text-ink">{g.libelle} · {g.duree_ans} an{(g.duree_ans ?? 0) > 1 ? 's' : ''}</span>
                        <span className="flex items-center justify-between gap-2 text-dark/60">
                          jusqu'au {dateFr(g.fin)} <Pastille statut={g.statut} />
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

