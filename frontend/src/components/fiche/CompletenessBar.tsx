const NIVEAUX: Record<string, string> = {
  conseils_generaux: 'Conseils généraux',
  prediagnostic_qualitatif: 'Pré-diagnostic qualitatif débloqué',
  preaudit_chiffre: 'Pré-audit chiffré débloqué',
}

export default function CompletenessBar({ score, niveau }: { score: number; niveau: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-8">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-semibold">Score de complétude de votre fiche</h2>
        <span className="text-2xl font-bold text-primary">{score}%</span>
      </div>
      <div className="h-3 rounded-full bg-gray-200 overflow-hidden mb-3">
        <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${score}%` }} />
      </div>
      <p className="text-sm text-gray-700">
        <strong>{NIVEAUX[niveau] ?? niveau}</strong> — plus vous renseignez votre maison, plus le conseil
        d'Helios est précis. Seuils : 40 % pour un pré-diagnostic qualitatif, 70 % pour un pré-audit chiffré.
      </p>
    </div>
  )
}
