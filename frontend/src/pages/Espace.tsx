import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Home, Sun, FileText, Zap, Handshake, Settings, Droplets, Building2, Wind, Sprout,
  FolderOpen, MessageCircle, LayoutGrid, Sparkles,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'
import { Skeleton, SkeletonCards } from '../components/Skeleton'
import ApiError from '../components/ApiError'
import HouseDocuments from '../components/fiche/HouseDocuments'
import BlocHelios from '../components/chat/BlocHelios'
import MarqueHelios from '../components/MarqueHelios'
import { RailOnglets, BandeOnglets, type OngletRail } from '../components/RailOnglets'

/** La même photo que le héros de l'accueil — un seul fichier pour toute la marque. */
const PHOTO = '/maison-hero.webp'

const NIVEAU_LABEL: Record<string, string> = {
  conseils_generaux: 'Conseils généraux',
  prediagnostic_qualitatif: 'Pré-diagnostic qualitatif',
  preaudit_chiffre: 'Pré-audit chiffré',
}

/* LE RAIL NE PORTE QUE CE QUI VIT SUR CETTE PAGE. Les autres écrans de l'espace
   (pré-audits, énergie, partenaires, pro) sont de vraies pages : en faire des onglets
   donnerait un `tablist` dont la moitié des onglets quittent la page, ce qui ment au
   clavier comme au lecteur d'écran. Ils sont rassemblés dans l'onglet « Le reste ». */
type Section = 'helios' | 'maison' | 'simulateurs' | 'documents' | 'reste'

const ONGLETS: OngletRail<Section>[] = [
  { id: 'helios', label: 'Helios', Icone: MessageCircle },
  { id: 'maison', label: 'Ma maison', Icone: Home },
  { id: 'simulateurs', label: 'Simuler', Icone: LayoutGrid },
  { id: 'documents', label: 'Papiers', Icone: FolderOpen },
  { id: 'reste', label: 'Le reste', Icone: Sparkles },
]

const SIMULATEURS = [
  { to: '/simulateur-solaire', icon: Sun, title: 'Potentiel solaire', desc: 'PV, batterie, tarifs' },
  { to: '/potentiel-hydrique', icon: Droplets, title: 'Potentiel hydrique', desc: 'Eau atmosphérique' },
  { to: '/espace/jardin', icon: Sprout, title: 'Mes cultures', desc: 'Le potager mois par mois' },
]

const AUTRES_TUILES = [
  { to: '/mon-espace', icon: Home, title: 'Ma fiche maison', desc: 'Compléter mon logement' },
  { to: '/espace/audits', icon: FileText, title: 'Mes pré-audits', desc: 'Diagnostic chiffré' },
  { to: '/espace/energie', icon: Zap, title: "Mon contrat d'énergie", desc: 'Conseil & SOBRY' },
  { to: '/espace/mises-en-relation', icon: Handshake, title: 'Mises en relation', desc: 'Partenaires travaux' },
  { to: '/espace/pro', icon: Building2, title: 'Espace Pro', desc: 'Énergie de mon entreprise' },
]

/** Une tuile, resserrée : icône et titre sur une ligne, la précision dessous. */
function Tuile({ to, icon: Icon, title, desc }: {
  to: string; icon: typeof Sun; title: string; desc: string
}) {
  return (
    <Link to={to}
      className="flex items-start gap-3 rounded-xl border border-bord bg-white px-3.5 py-3
                 transition-colors hover:border-primary hover:bg-cream">
      <Icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
      <span className="min-w-0">
        <span className="block text-sm font-semibold leading-tight text-ink">{title}</span>
        <span className="block text-xs leading-snug text-dark/60">{desc}</span>
      </span>
    </Link>
  )
}

export default function Espace() {
  useTitle('Mon espace')
  const { user, authFetch } = useAuth()
  /* Arrivee depuis « Demander l'avis d'Helios » (un document de la fiche) :
     `?ask=<question>` pre-remplit le champ de la conversation. C'est l'ancienne
     adresse `/espace/helios?ask=` qui aboutit ici depuis la fusion des deux pages. */
  const [searchParams] = useSearchParams()
  const askPrefill = searchParams.get('ask') ?? undefined
  /* `?ask=` vise la conversation : on ouvre son onglet, sinon la question pre-remplie
     attendrait derriere un onglet ferme. */
  const [section, setSection] = useState<Section>('helios')
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
    <section className="max-w-[1040px] mx-auto px-4 py-8">
      {/* L'EN-TÊTE PHOTO. La page s'ouvrait sur un titre nu au-dessus d'un grand pavé de
          couleur : juste, mais froid. La photo du carnet de maison est celle de l'accueil,
          donc on reste chez soi en se connectant.

          Le voile part de l'ivoire PLEIN à gauche et décroît jusqu'à transparent : le texte
          est posé sur l'ivoire, la photo respire à droite. Comme sur l'accueil, le dégradé
          se termine sur `rgb(var(--h-sable) / 0)` et JAMAIS sur `transparent` — en CSS
          `transparent` vaut du noir transparent, et l'interpolation salit tout le raccord. */}
      <div className="relative mb-5 overflow-hidden rounded-2xl border border-bord">
        <img src={PHOTO} alt="" aria-hidden="true" loading="lazy" width={1536} height={1024}
          className="h-28 w-full object-cover object-[center_35%] sm:h-36" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgb(var(--h-sable))_0%,rgb(var(--h-sable)/0.92)_38%,rgb(var(--h-sable)/0.55)_68%,rgb(var(--h-sable)/0)_100%)]" />
        <div className="absolute inset-0 flex items-center justify-between gap-3 px-5 sm:px-6">
          <div className="min-w-0">
            <h1 className="font-display text-2xl leading-tight text-ink sm:text-3xl">
              Bonjour {user?.prenom || ''}
            </h1>
            <p className="mt-0.5 text-sm text-dark/70">
              {house ? 'Votre carnet de maison vous attend.' : 'Bienvenue — commençons par votre logement.'}
            </p>
          </div>
          <Link to="/espace/compte"
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-bord
                       bg-white/80 px-2.5 py-1.5 text-xs text-dark/70 backdrop-blur-sm
                       hover:border-primary hover:text-primary">
            <Settings className="h-3.5 w-3.5" /> <span className="hidden sm:inline">Mon compte</span>
          </Link>
        </div>
      </div>

      {loading ? (
        <>
          <Skeleton className="h-12 w-full mb-4" />
          <SkeletonCards count={4} />
        </>
      ) : error ? (
        <ApiError retry={load} />
      ) : (
        <>
          <BandeOnglets onglets={ONGLETS} actif={section} onChoisir={setSection}
            ariaLabel="Sections de mon espace" />

          <div className="grid items-start gap-4 md:grid-cols-[4.75rem_minmax(0,1fr)]">
            <RailOnglets onglets={ONGLETS} actif={section} onChoisir={setSection}
              ariaLabel="Sections de mon espace" />

            <div id="panneau-espace" role="tabpanel" className="min-w-0">
              {/* La conversation RESTE MONTÉE quelle que soit la section : la démonter
                  perdrait les messages à l'écran et l'identifiant de conversation dès
                  qu'on va voir ses documents. On la cache, on ne la supprime pas. */}
              <div className={section === 'helios' ? '' : 'hidden'}>
                <BlocHelios askPrefill={askPrefill} />
              </div>

              {section === 'maison' && (
                <div className="rounded-xl border border-ink/10 bg-white p-4">
                  {house ? (
                    <>
                      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                        <span className="font-display text-4xl leading-none text-primary">
                          {house.completeness_score}%
                        </span>
                        <span className="text-sm text-dark/60">de votre fiche ({house.code_postal})</span>
                      </div>
                      <p className="mt-2 text-sm text-dark/70">
                        Niveau : {NIVEAU_LABEL[house.niveau] ?? house.niveau}
                        {lastAudit && ` · dernier pré-audit le ${new Date(lastAudit.created_at).toLocaleDateString('fr-FR')}`}
                      </p>
                      <p className="mt-3 text-sm text-dark/70">
                        Chaque champ rempli affine les conseils d'Helios. Les blocs se remplissent
                        dans l'ordre que vous voulez, et rien n'est obligatoire à part le code postal.
                      </p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Link to="/mon-espace"
                          className="rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90">
                          Compléter ma fiche
                        </Link>
                        {house.completeness_score >= 70 && (
                          <Link to="/espace/audits"
                            className="rounded-lg border border-primary px-3.5 py-2 text-sm font-semibold text-primary hover:bg-primary/5">
                            Générer un pré-audit
                          </Link>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        {/* Premier contact avec un espace vide : la marque tient la place
                            d'un interlocuteur devant une page encore à remplir. */}
                        <MarqueHelios taille={30} className="shrink-0 text-primary" />
                        <div>
                          <p className="text-sm font-semibold text-ink">Commençons par votre logement.</p>
                          <p className="text-xs text-dark/60">3 questions suffisent — Helios s'occupe du reste.</p>
                        </div>
                      </div>
                      <Link to="/mon-espace"
                        className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                        Répondre aux 3 questions
                      </Link>
                    </div>
                  )}
                </div>
              )}

              {section === 'simulateurs' && (
                <div className="grid gap-2 sm:grid-cols-2">
                  {SIMULATEURS.map((t) => <Tuile key={t.to} {...t} />)}
                  <div className="flex items-start gap-3 rounded-xl border border-dashed border-bord px-3.5 py-3 opacity-70">
                    <Wind className="mt-0.5 h-5 w-5 shrink-0 text-dark/40" />
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold leading-tight text-dark/60">Potentiel éolien</span>
                      <span className="block text-xs leading-snug text-dark/40">Eolia — bientôt</span>
                    </span>
                  </div>
                </div>
              )}

              {section === 'documents' && (
                <div className="rounded-xl border border-ink/10 bg-white p-4">
                  <p className="mb-3 text-sm text-dark/70">
                    DPE, factures, devis — Helios peut les relire avec vous.
                  </p>
                  <HouseDocuments />
                </div>
              )}

              {section === 'reste' && (
                <div className="grid gap-2 sm:grid-cols-2">
                  {AUTRES_TUILES.map((t) => <Tuile key={t.to} {...t} />)}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  )
}
