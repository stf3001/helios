import Hero from '../components/Hero'
import Card from '../components/Card'

export default function HeliosIA() {
  return (
    <>
      <Hero title="Helios. Une IA franche, dénuée d'intérêt." />
      <section className="max-w-[900px] mx-auto px-4 py-12 text-lg text-gray-700">
        <p>
          Helios est notre intelligence artificielle dédiée à l'habitat et à l'énergie. Sa particularité ne
          tient pas à sa technologie, mais à sa constitution : un ensemble de règles publiques qui lui
          interdisent de pousser un produit, de favoriser un partenaire ou d'inventer un chiffre.
        </p>
      </section>
      <section className="max-w-[1100px] mx-auto px-4 pb-12 grid gap-6 md:grid-cols-2">
        <Card title="Ce qu'Helios fait">
          Répond à vos questions sur l'énergie, les travaux, les aides · analyse votre logement et priorise
          selon vos objectifs · estime économies, coûts et aides en ordres de grandeur · vous oriente vers
          des professionnels certifiés quand c'est nécessaire.
        </Card>
        <Card title="Ce qu'Helios ne fait jamais">
          Vendre ou survendre quoi que ce soit · donner un chiffre certain là où il y a une incertitude ·
          proposer un partenaire sans votre accord · se faire passer pour un audit réglementaire.
        </Card>
      </section>
      <section className="max-w-[900px] mx-auto px-4 pb-14">
        <div className="rounded-2xl border-2 border-dashed border-primary/40 p-8 text-center text-gray-500">
          Le chat public Helios arrive ici (jalon 3). <br />
          « Bonjour, je suis Helios. Posez-moi vos questions sur l'énergie de votre logement… »
        </div>
      </section>
    </>
  )
}
