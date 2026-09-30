/** En-tete de page commun (une dizaine de pages l'utilisent).
 *
 * Il ne porte plus d'aplat colore : dans le langage « carnet de maison », une page
 * s'ouvre sur du blanc de papier et un titre serif, pas sur un bandeau. Le filet
 * du bas remplace la rupture que faisait la couleur. */
export default function Hero({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <section className="border-b border-bord">
      <div className="max-w-[900px] mx-auto px-4 py-14 md:py-16 text-center">
        <h1 className="font-display text-4xl md:text-5xl lg:text-[56px] leading-[1.08] text-ink">{title}</h1>
        {subtitle && <p className="mt-4 text-lg text-gray-600 max-w-[620px] mx-auto">{subtitle}</p>}
      </div>
    </section>
  )
}
