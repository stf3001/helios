export default function Footer() {
  return (
    <footer className="bg-dark text-gray-300 mt-16">
      <div className="max-w-[1200px] mx-auto px-4 py-10 grid gap-8 md:grid-cols-3 text-sm">
        <div>
          <p className="font-bold text-white text-lg mb-2">HELIOS</p>
          <p>Diagnostic énergétique assisté par IA. Gratuit, indépendant, à votre rythme.</p>
        </div>
        <div>
          <p className="font-semibold text-white mb-2">Transparence</p>
          <p>HELIOS est gratuit pour vous, toujours. La plateforme se rémunère par une commission versée
             par les entreprises partenaires — jamais par le client. Les conseils d'Helios sont indépendants.</p>
        </div>
        <div>
          <p className="font-semibold text-white mb-2">« Je le sais, mais je fais ma part. »</p>
          <p>L'esprit colibri guide chacun de nos conseils : aucun geste n'est trop petit.</p>
        </div>
      </div>
      <div className="border-t border-gray-700 py-4 text-center text-xs text-gray-500">
        © 2026 HELIOS — Mentions légales · CGU · Confidentialité (à venir)
      </div>
    </footer>
  )
}
