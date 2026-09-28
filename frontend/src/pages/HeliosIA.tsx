import { useSearchParams } from 'react-router-dom'
import Hero from '../components/Hero'
import Card from '../components/Card'
import ChatWidget from '../components/chat/ChatWidget'
import { useTitle } from '../hooks/useTitle'

export default function HeliosIA() {
  useTitle('Helios — votre assistant énergie')
  // ?q= : arrivée depuis le champ de saisie du hero de l'accueil → question pré-remplie
  // (l'utilisateur garde la main : il relit et envoie lui-même).
  const [searchParams] = useSearchParams()
  const initialQuestion = searchParams.get('q') ?? undefined
  return (
    <>
      {/* Le propos est monté DANS le bandeau : le titre seul ne disait rien de ce qui
          distingue Helios, et le paragraphe qui le disait vraiment attendait en dessous,
          en gris, là où on ne le lit pas. Un bandeau, une idée.

          Les quatre valeurs citées sont les quatre piliers de `01-CHARTE-HELIOS.md`, mot
          pour mot. Si la charte change, c'est ici qu'il faut revenir. */}
      <Hero
        title="L'IA au service de votre foyer"
        subtitle="Dédiée à l'habitat et à l'énergie. Sa particularité n'est pas sa technologie, mais sa constitution : des règles et des valeurs — transparence, humilité, honnêteté, excellence."
      />
      {/* La conversation d'abord : c'est ce pour quoi on vient. */}
      <section className="max-w-[900px] mx-auto px-4 pt-12 pb-6">
        <ChatWidget initialInput={initialQuestion} />
      </section>
      {/* Les deux cartes sont un CONTRAT : ce qu'il fait, ce qu'il ne fera jamais. Elles
          se lisent après avoir eu envie de lui parler, pas avant. Posées entre le bandeau
          et la conversation, elles obligeaient à traverser une page de doctrine pour
          atteindre le champ de saisie. */}
      <section className="max-w-[1100px] mx-auto px-4 pb-14 grid gap-6 md:grid-cols-2">
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
    </>
  )
}
