import Hero from '../components/Hero'

const engagements = [
  'Certifications à jour (RGE quand les aides l\'exigent), assurance décennale',
  'Transparence des prix : devis détaillés, sans frais cachés, délais tenus',
  'Aucun démarchage hors demande explicite, pas de vente forcée',
  'Travaux conformes aux règles de l\'art, SAV réactif',
  'Acceptation de la notation par les clients',
  'Un partenaire qui ne respecte plus la charte est déréférencé — sans exception',
]

export default function Partenaires() {
  return (
    <>
      <Hero title="Des entreprises choisies, une charte exigeante." />
      <section className="max-w-[800px] mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold mb-6">La charte partenaire</h2>
        <ul className="space-y-3">
          {engagements.map((e, i) => (
            <li key={i} className="flex gap-3 text-gray-700">
              <span className="text-primary font-bold">✓</span> {e}
            </li>
          ))}
        </ul>
        <div className="mt-10 border-l-4 border-primary bg-gray-50 rounded-r-2xl p-6 text-gray-700">
          <strong>Transparence.</strong> Les partenaires versent à HELIOS une commission d'apport d'affaires
          quand un client leur confie des travaux via la plateforme. Cette commission ne modifie jamais les
          préconisations d'Helios, et n'est jamais facturée au client.
        </div>
        <p className="mt-10 text-gray-500 text-center">Annuaire des partenaires — à venir (jalon 8).</p>
      </section>
    </>
  )
}
