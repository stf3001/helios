const NIVEAUX: Record<string, string> = {
  conseils_generaux: 'Conseils généraux',
  prediagnostic_qualitatif: 'Pré-diagnostic qualitatif débloqué',
  preaudit_chiffre: 'Pré-audit chiffré débloqué',
}

/** Encouragement bienveillant selon l'avancement (esprit colibri). */
function encouragement(score: number): string {
  if (score === 0) return "C'est parti ! Chaque champ que vous renseignez aide Helios à mieux vous conseiller."
  if (score < 40) return 'Beau début 🌱 Encore quelques champs et Helios pourra établir un premier pré-diagnostic.'
  if (score < 70) return 'Bravo, vous avez débloqué le pré-diagnostic ! Continuez pour obtenir un pré-audit chiffré.'
  if (score < 100) return 'Excellent 👏 Votre fiche est très complète — le pré-audit chiffré est disponible.'
  return 'Fiche complète à 100 % 🎉 Helios a toutes les cartes en main pour vous conseiller au mieux.'
}

export default function CompletenessBar({ score, niveau }: { score: number; niveau: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-8">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-semibold">Score de complétude de votre fiche</h2>
        <span className="text-2xl font-bold text-primary">{score}%</span>
      </div>
      <div className="h-3 rounded-full bg-gray-200 overflow-hidden mb-3">
        <div className="h-full bg-gradient-to-r from-sun to-primary rounded-full transition-all duration-500" style={{ width: `${score}%` }} />
      </div>
      <p className="text-sm font-medium text-ink mb-1">{encouragement(score)}</p>
      <p className="text-sm text-gray-600">
        <strong>{NIVEAUX[niveau] ?? niveau}</strong> — seuils : 40 % pour un pré-diagnostic qualitatif,
        70 % pour un pré-audit chiffré.
      </p>
    </div>
  )
}
