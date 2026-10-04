import { Link } from 'react-router-dom'
import { ArrowRight, House } from 'lucide-react'

/**
 * Le constat d'Helios, posé sur la photo du héros.
 *
 * CE QUE CE N'EST PAS, ET POURQUOI. La maquette de départ posait ici un tableau
 * de bord : identité, trois chiffres, quatre équipements avec leur état, douze
 * mois de consommation, puis la recommandation. 730 px de haut. Trois raisons de
 * l'avoir abandonne :
 *
 * 1. **Un tableau de bord promet du travail.** Un visiteur qui trouve sa facture
 *    pénible voit douze lignes à remplir, pas un service. C'est l'inverse de ce
 *    que vend Helios.
 * 2. **C'est la maison d'un autre.** Plus la carte montre de données, plus elle
 *    parle de quelqu'un d'autre — et moins le visiteur s'y reconnait.
 * 3. **Ce qui convainc, c'est la CONCLUSION, pas l'inventaire.** Personne ne se
 *    décide devant « combles 30 cm · 2019 ». On se décide devant 450 € par an.
 *
 * Il reste donc deux choses, et c'est tout l'argument : **Helios sait de quelle
 * maison on parle** (l'identité), et **il en tire quelque chose d'utile** (le
 * constat chiffré). Le reste appartient à l'espace client, pas à l'accueil.
 *
 * DEUX RÈGLES CONSERVÉES :
 * - **La carte dit qu'elle est un exemple.** La charte (doc 01) interdit de faire
 *   passer de l'inventé pour du réel, et `TODO.md` compte déjà deux points
 *   bloquants de cette nature. La pastille n'est pas un ornement.
 * - **Les unités sont justes.** Le kWc est une puissance installée, jamais une
 *   production : la maquette affichait « Production : 4,8 kWc ».
 */

/** Les deux points qui justifient le constat du bas. Chauffage gaz + ballon
 *  électrique : le cas le plus courant du parc français, et celui qui rend
 *  crédibles les 450 €. La maquette posait une pompe à chaleur à côté de
 *  radiateurs à gaz, ce qui se contredisait. */
const A_SURVEILLER = ['Chaudière gaz · 2009', 'Ballon électrique · 2011']

export default function CarteMaison() {
  return (
    <div className="rounded-2xl border border-bord bg-white/95 backdrop-blur-sm p-5 shadow-question">
      {/* --- De quelle maison on parle --- */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="grid place-items-center w-10 h-10 rounded-xl bg-cream shrink-0">
            <House className="w-[18px] h-[18px] text-ink" strokeWidth={1.5} aria-hidden="true" />
          </span>
          <span className="min-w-0">
            <span className="block font-display text-lg text-ink leading-tight">Ma maison</span>
            {/* Pas de `truncate` : la carte est étroite (300 px), et une identité
                coupée à « 1998 · 4,... » ne prouve plus rien. Elle se replie sur
                deux lignes, ce qui ne coûte que de la hauteur — dont la carte a
                justement besoin pour se tenir contre le bord de la photo. */}
            <span className="block text-[13px] text-gray-600 leading-snug">
              Toulon · 120 m² · 1998 · 4,8 kWc
            </span>
          </span>
        </div>
        <span className="shrink-0 rounded-full border border-bord bg-sable px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-gray-600">
          Exemple
        </span>
      </div>

      {/* --- Ce qu'Helios y a repéré. L'état est ÉCRIT, jamais porté par la seule
              couleur : la maquette posait un point gris que rien n'expliquait. --- */}
      <div className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <span className="text-[13px] text-gray-600">2 points à surveiller :</span>
        {A_SURVEILLER.map((p) => (
          <span
            key={p}
            className="inline-flex items-center gap-1.5 rounded-full bg-sable px-2.5 py-1 text-[12px] text-ink"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-gray-300" aria-hidden="true" />
            {p}
          </span>
        ))}
      </div>

      {/* --- La conclusion : le seul chiffre de l'accueil, dit une seule fois.
              La maquette le répétait dans une bulle de conversation ET ici ;
              répéter un chiffre fort ne le double pas, il le divise. --- */}
      <Link
        to="/inscription"
        aria-label="Créer mon espace pour obtenir le constat de ma maison"
        className="group mt-4 block rounded-xl border border-primary/25 bg-primary/[0.06] px-4 py-3 hover:bg-primary/10 transition-colors"
      >
        <span className="block text-sm text-ink leading-relaxed">
          Un ballon thermodynamique ferait économiser{' '}
          <strong className="font-semibold text-primary">jusqu’à 450 € par an</strong>.
        </span>
        <span className="mt-1.5 inline-flex items-center gap-1.5 text-[13px] font-semibold text-primary group-hover:gap-2.5 transition-all">
          Voir le conseil <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
        </span>
      </Link>
    </div>
  )
}
