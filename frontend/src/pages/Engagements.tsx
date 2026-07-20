import { Link } from 'react-router-dom'
import { ShieldCheck, Scale, Calculator, Lock, HeartHandshake, Megaphone } from 'lucide-react'
import Hero from '../components/Hero'
import { useTitle } from '../hooks/useTitle'

// Chaque engagement correspond à un garde-fou réellement appliqué DANS LE CODE
// (constitution v0.2) — cette page ne promet rien qui ne soit pas implémenté.
const ENGAGEMENTS = [
  {
    icon: Scale,
    titre: 'Notre avis d\'abord — et il peut être négatif',
    texte:
      'Avant toute mise en relation ou offre partenaire, Helios vous donne son avis indépendant. ' +
      'S\'il est défavorable, nous vous le disons — et nous ne vous proposons pas le partenaire. ' +
      'Nous vous dirons aussi quand la meilleure option est de ne rien faire.',
  },
  {
    icon: HeartHandshake,
    titre: 'Jamais un euro facturé au client',
    texte:
      'HELIOS est gratuit pour vous, toujours. Nous nous rémunérons par une commission versée par ' +
      'les entreprises partenaires quand un chantier se signe — jamais par vous, et cette commission ' +
      'ne modifie jamais nos préconisations.',
  },
  {
    icon: Calculator,
    titre: 'Des chiffres calculés, pas générés',
    texte:
      'Tous les montants (pré-audits, simulateur solaire, économies estimées) sortent de moteurs de ' +
      'calcul déterministes fondés sur des données de référence — jamais d\'une IA générative. ' +
      'Et ils sont donnés en fourchettes, car un chiffre certain serait un mensonge.',
  },
  {
    icon: Megaphone,
    titre: 'Le comparateur public toujours cité',
    texte:
      'Pour tout ce qui touche à votre contrat d\'énergie, nous citons systématiquement le comparateur ' +
      'public et indépendant energie-info.fr, pour que vous puissiez vérifier par vous-même.',
  },
  {
    icon: Lock,
    titre: 'Vos données vous appartiennent',
    texte:
      'Consentement explicite et horodaté avant toute transmission à un partenaire, retirable tant que rien ' +
      'n\'est signé. Export complet de vos données et suppression de compte en un clic depuis votre espace. ' +
      'Votre numéro de compteur (PDL) n\'est jamais transmis aux modèles d\'IA.',
  },
  {
    icon: ShieldCheck,
    titre: 'Aucun démarchage',
    texte:
      'Personne ne vous appellera sans que vous l\'ayez demandé. Un partenaire qui démarche hors demande ' +
      'explicite ou ne respecte plus la charte est déréférencé — sans exception.',
  },
]

export default function Engagements() {
  useTitle('Nos engagements')
  return (
    <>
      <Hero
        title="Nos engagements"
        subtitle="Pas des promesses marketing : des règles inscrites dans le fonctionnement même d'Helios."
      />
      <section className="max-w-[900px] mx-auto px-4 py-12">
        <div className="grid sm:grid-cols-2 gap-4">
          {ENGAGEMENTS.map((e) => (
            <div key={e.titre} className="border border-gray-200 rounded-2xl p-6">
              <e.icon className="w-7 h-7 text-primary mb-3" />
              <h2 className="font-display font-semibold text-ink mb-2">{e.titre}</h2>
              <p className="text-sm text-gray-600">{e.texte}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 border-l-4 border-primary bg-gray-50 rounded-r-2xl p-6 text-gray-700 text-sm">
          Ces règles sont écrites dans la « constitution » d'Helios, versionnée et appliquée dans le code de la
          plateforme. Gérer mes données : <Link to="/espace/compte" className="text-primary underline">mon compte</Link> ·
          Comprendre notre modèle : <Link to="/comment-ca-marche" className="text-primary underline">comment ça marche</Link>.
        </div>
      </section>
    </>
  )
}
