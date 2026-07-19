import Hero from '../components/Hero'
import Card from '../components/Card'
import HierarchieColibri from '../components/HierarchieColibri'

export default function CommentCaMarche() {
  return (
    <>
      <Hero title="Comment ça marche" subtitle="Trois étapes, à votre rythme." />
      <section className="max-w-[1100px] mx-auto px-4 py-12 grid gap-6 md:grid-cols-3">
        <Card title="1. Décrivez votre maison">
          Créez votre espace gratuit et renseignez votre logement : année, surface, chauffage, isolation…
          Tout est optionnel, tout est modifiable. Votre score de complétude vous montre ce qui affinerait
          le diagnostic.
        </Card>
        <Card title="2. Helios analyse">
          Dès 40 % de complétude, Helios établit un pré-diagnostic : points faibles probables, ordre de
          priorité des travaux. À 70 %, il chiffre les ordres de grandeur : économies, coûts, aides,
          temps de retour.
        </Card>
        <Card title="3. Agissez à votre rythme">
          Commencez par les gestes gratuits, planifiez les travaux selon votre budget. Si vous le souhaitez,
          Helios vous met en relation avec une entreprise partenaire signataire de notre charte.
        </Card>
      </section>
      <section className="bg-cream py-14">
        <div className="max-w-[900px] mx-auto px-4">
          <h2 className="text-2xl font-bold text-center mb-2">La hiérarchie qui guide chaque conseil</h2>
          <HierarchieColibri />
        </div>
      </section>

      <section className="max-w-[900px] mx-auto px-4 py-12">
        <div className="border-l-4 border-primary bg-cream rounded-r-2xl p-6 text-gray-700">
          Le pré-diagnostic Helios est indicatif : il ne remplace pas un audit énergétique réglementaire
          réalisé par un professionnel certifié. Il vous aide à le préparer — et à le comprendre.
        </div>
      </section>
    </>
  )
}
