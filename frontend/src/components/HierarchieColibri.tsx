import { Leaf, ShieldCheck, Flame, Sun } from 'lucide-react'

/** La hiérarchie de conseil d'Helios (constitution §3) : toujours dans cet ordre.
 *  Réutilisable sur l'accueil, « Comment ça marche », les pré-audits. */

const ETAPES = [
  {
    n: 1, icon: Leaf, color: 'text-leaf', ring: 'bg-leaf/10 border-leaf/30',
    titre: 'Sobriété',
    desc: 'Les gestes gratuits d\'abord : réglages, température, programmation. Rien à acheter.',
  },
  {
    n: 2, icon: ShieldCheck, color: 'text-sky', ring: 'bg-sky/10 border-sky/30',
    titre: 'Isolation',
    desc: 'On isole avant tout : on n\'installe pas une pompe à chaleur dans une passoire.',
  },
  {
    n: 3, icon: Flame, color: 'text-primary', ring: 'bg-primary/10 border-primary/30',
    titre: 'Systèmes performants',
    desc: 'Chauffage, eau chaude, ventilation, régulation : une fois la maison bien isolée.',
  },
  {
    n: 4, icon: Sun, color: 'text-sun', ring: 'bg-sun/10 border-sun/40',
    titre: 'Production',
    desc: 'Le solaire en dernier — quand vos besoins sont déjà réduits au minimum.',
  },
]

export default function HierarchieColibri({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? '' : 'py-2'}>
      {!compact && (
        <p className="text-center text-gray-600 mb-8 max-w-xl mx-auto">
          Helios raisonne toujours dans cet ordre — du geste gratuit au gros chantier.
          On ne vous vendra jamais l'étape&nbsp;4 si l'étape&nbsp;1 suffit.
        </p>
      )}
      <ol className="relative max-w-2xl mx-auto space-y-3">
        {ETAPES.map((e) => (
          <li key={e.n} className={`flex items-start gap-4 rounded-2xl border p-4 sm:p-5 ${e.ring}`}>
            <div className={`shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-white ${e.color}`}>
              <e.icon className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-bold ${e.color}`}>ÉTAPE {e.n}</span>
                <h3 className="font-display font-semibold text-ink text-lg leading-tight">{e.titre}</h3>
              </div>
              <p className="text-sm text-gray-600 mt-1">{e.desc}</p>
            </div>
          </li>
        ))}
      </ol>
      {!compact && (
        <p className="text-center text-xs text-gray-400 mt-6">
          « Je le sais, mais je fais ma part. » — l'esprit colibri : aucun geste n'est trop petit.
        </p>
      )}
    </div>
  )
}
