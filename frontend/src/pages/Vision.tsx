import Hero from '../components/Hero'
import Card from '../components/Card'

export default function Vision() {
  return (
    <>
      <Hero title="Rendre la transition énergétique simple, honnête et accessible à chaque foyer." />
      <section className="max-w-[900px] mx-auto px-4 py-12 space-y-4 text-lg text-gray-700">
        <p>
          La rénovation énergétique est devenue un labyrinthe : aides qui changent chaque année, démarchage
          agressif, devis incompréhensibles, conseils orientés par celui qui vend. Résultat : des millions de
          foyers renoncent, ou se trompent de travaux.
        </p>
        <p>
          Nous croyons qu'un foyer bien informé fait les bons choix. HELIOS met la puissance de l'intelligence
          artificielle au service de cette conviction : un conseiller disponible à toute heure, qui connaît les
          normes et les aides, qui s'adapte à VOTRE maison, VOS objectifs, VOTRE budget — et qui n'a rien à
          vous vendre.
        </p>
      </section>
      <section className="max-w-[1100px] mx-auto px-4 pb-14 grid gap-6 md:grid-cols-2">
        <Card title="Transparence">Notre modèle économique est affiché, nos préconisations sont expliquées. Jamais de boîte noire.</Card>
        <Card title="Honnêteté">Si le meilleur conseil est « ne faites rien », Helios vous le dira. Les chiffres sont donnés en fourchettes, avec leurs incertitudes.</Card>
        <Card title="Excellence">Une base de connaissances entretenue en continu, des sources fiables, des partenaires exigeants et contrôlés.</Card>
        <Card title="Humilité">Helios oriente, il ne remplace ni un audit réglementaire ni un bureau d'études. Nous connaissons nos limites et le disons.</Card>
      </section>
    </>
  )
}
