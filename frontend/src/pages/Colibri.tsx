import Hero from '../components/Hero'

export default function Colibri() {
  return (
    <>
      <Hero title="L'esprit colibri" subtitle="Chaque geste compte." />
      <section className="max-w-[800px] mx-auto px-4 py-12 space-y-4 text-lg text-gray-700">
        <p className="italic">
          La légende raconte qu'au milieu d'un incendie de forêt, un colibri transportait quelques gouttes
          d'eau dans son bec. « Tu vois bien que ce n'est pas avec ces gouttes que tu vas éteindre le feu ! »
        </p>
        <p className="text-2xl font-semibold text-dark text-center py-4">« Je le sais, mais je fais ma part. »</p>
        <p>
          Un thermostat bien réglé, dix centimètres d'isolant, un panneau solaire : aucun geste n'est trop
          petit pour la planète. HELIOS existe pour que chaque foyer puisse faire sa part — intelligemment,
          à son rythme, sans se ruiner. L'IA est notre goutte d'eau : mise gratuitement au service de tous,
          elle démultiplie ce que chacun peut faire.
        </p>
      </section>
      {/* Compteurs d'impact — branchés sur l'API au jalon 4 (foyers accompagnés, MWh économisés, CO2 évité) */}
    </>
  )
}
