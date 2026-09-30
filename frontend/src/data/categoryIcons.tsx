import type { LucideIcon } from 'lucide-react'
import {
  BatteryCharging, Battery, Building2, Car, Compass, Cpu, DoorClosed, Droplet,
  Droplets, FileBarChart, Flame, HandCoins, HardHat, Key, Layers, Leaf, Scale, ShieldAlert,
  Smile, Sparkles, Sprout, Sun, Wind, Zap,
} from 'lucide-react'

/** Icône + couleur de marque par catégorie — fiches de connaissance (libellés capitalisés
 * français) et FAQ (`/api/faq`, clés en minuscules sans accent) partagent ce même mapping,
 * normalisé via `normalizeCat`. Couleurs = tokens `tailwind.config.js` (primary/ink/sky/leaf/
 * sun/terra), pas de couleur inventée. Catégorie inconnue → fallback neutre, jamais d'erreur. */

interface CatIcon {
  Icon: LucideIcon
  color: string // classe Tailwind text-*
}

const MAP: Record<string, CatIcon> = {
  isolation: { Icon: Layers, color: 'text-terra' },
  chauffage: { Icon: Flame, color: 'text-primary' },
  photovoltaique: { Icon: Sun, color: 'text-primary' },
  solaire: { Icon: Sun, color: 'text-primary' },
  energie: { Icon: Zap, color: 'text-primary' },
  achat_energie: { Icon: Zap, color: 'text-primary' },
  locataire: { Icon: Key, color: 'text-ink' },
  copropriete: { Icon: Building2, color: 'text-ink' },
  dpe: { Icon: FileBarChart, color: 'text-ink' },
  chantier: { Icon: HardHat, color: 'text-terra' },
  eau: { Icon: Droplet, color: 'text-sky' },
  ecs: { Icon: Droplets, color: 'text-sky' },
  mobilite: { Icon: Car, color: 'text-leaf' },
  ve: { Icon: Car, color: 'text-leaf' },
  aides: { Icon: HandCoins, color: 'text-primary' },
  financement: { Icon: HandCoins, color: 'text-primary' },
  pilotage: { Icon: Cpu, color: 'text-ink' },
  autoconso: { Icon: BatteryCharging, color: 'text-primary' },
  stockage: { Icon: Battery, color: 'text-primary' },
  ventilation: { Icon: Wind, color: 'text-sky' },
  eolien: { Icon: Wind, color: 'text-sky' },
  menuiseries: { Icon: DoorClosed, color: 'text-terra' },
  reglementation: { Icon: Scale, color: 'text-ink' },
  confort: { Icon: Smile, color: 'text-leaf' },
  sobriete: { Icon: Leaf, color: 'text-leaf' },
  jardin: { Icon: Sprout, color: 'text-leaf' },
  vision: { Icon: Compass, color: 'text-ink' },
  helios: { Icon: Sparkles, color: 'text-primary' },
  vigilance: { Icon: ShieldAlert, color: 'text-terra' },
  renovation: { Icon: HardHat, color: 'text-terra' },
}

const FALLBACK: CatIcon = { Icon: Sparkles, color: 'text-gray-400' }

/** "Copropriété" / "copropriete" / "COPROPRIETE" -> "copropriete". */
function normalizeCat(cat: string): string {
  return cat
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z]/g, '_')
    .replace(/^_+|_+$/g, '')
}

export function getCategoryIcon(cat: string | null | undefined): CatIcon {
  if (!cat) return FALLBACK
  return MAP[normalizeCat(cat)] ?? FALLBACK
}

/** Libelle affichable d'une categorie.
 *
 * La regle automatique (souligne -> espace, premiere lettre en capitale) suffit
 * pour « isolation » ou « chauffage », mais elle rend « Dpe », « Ecs », « Ve » et
 * « Photovoltaique ». Ces cas-la sont ecrits a la main ; les autres restent
 * derives, pour qu'une nouvelle categorie s'affiche correctement sans toucher
 * ce fichier. */
const LIBELLES: Record<string, string> = {
  achat_energie: "Achat d'énergie",
  autoconso: 'Autoconsommation',
  copropriete: 'Copropriété',
  dpe: 'DPE',
  ecs: 'Eau chaude',
  energie: 'Énergie',
  eolien: 'Éolien',
  mobilite: 'Mobilité',
  photovoltaique: 'Photovoltaïque',
  reglementation: 'Réglementation',
  sobriete: 'Sobriété',
  ve: 'Véhicule électrique',
}

export function libelleCategorie(cat: string): string {
  const cle = normalizeCat(cat)
  if (LIBELLES[cle]) return LIBELLES[cle]
  const mots = cat.replace(/_/g, ' ')
  return mots.charAt(0).toUpperCase() + mots.slice(1)
}
