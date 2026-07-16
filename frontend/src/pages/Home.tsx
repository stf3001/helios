import { Link } from 'react-router-dom'
import Hero from '../components/Hero'
import Card from '../components/Card'

export default function Home() {
  return (
    <>
      <Hero
        title="Votre maison mérite un conseil franc."
        subtitle="Helios, notre intelligence artificielle indépendante, analyse votre logement et vous guide dans vos travaux d'énergie — gratuitement, sans rien à vous vendre, à votre rythme."
      />
      <section className="max-w-[1100px] mx-auto px-4 py-14 grid gap-6 md:grid-cols-3">
        <Card title="Un diagnostic assisté par IA">
          Décrivez votre maison, Helios identifie les points faibles et les priorités.
          Plus vous renseignez, plus le conseil est précis.
        </Card>
        <Card title="Des conseils sans intérêt caché">
          Helios ne vend rien. Si le meilleur conseil est un réglage gratuit, c'est ce qu'il vous dira.
        </Card>
        <Card title="Des artisans de confiance, si vous le souhaitez">
          Des entreprises partenaires signataires de notre charte. La mise en relation ne se fait
          que si vous la demandez.
        </Card>
      </section>
      <section className="bg-primary/5 py-12">
        <div className="max-w-[900px] mx-auto px-4 text-center">
          <p className="text-2xl font-semibold mb-2">« Je le sais, mais je fais ma part. »</p>
          <p className="text-gray-700">
            Chaque geste compte pour la planète — et pour votre facture. Helios vous aide à trouver le vôtre.{' '}
            <Link to="/colibri" className="text-primary font-semibold">L'esprit colibri →</Link>
          </p>
        </div>
      </section>
      <section className="max-w-[900px] mx-auto px-4 py-12">
        <div className="border-l-4 border-primary bg-gray-50 rounded-r-2xl p-6 text-gray-700">
          <strong>Transparence.</strong> HELIOS est gratuit pour vous, toujours. La plateforme se rémunère
          par une commission versée par les entreprises partenaires quand vous leur confiez des travaux.
          Les conseils d'Helios sont strictement indépendants de ce mécanisme — c'est écrit dans sa charte,
          et c'est non négociable.
        </div>
      </section>
    </>
  )
}
