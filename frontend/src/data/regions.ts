/**
 * Les régions métropolitaines et leurs départements.
 *
 * COPIE FIDÈLE DE `api/app/services/regions.py` — les deux se tiennent à jour ENSEMBLE.
 * Le découpage administratif ne bouge pas (c'est pourquoi la duplication est tenable) ;
 * ce qui pourrait bouger, c'est le périmètre annoncé : Corse comprise, outre-mer exclu.
 *
 * Pourquoi le front en a besoin : un partenaire est enregistré avec une liste de
 * DÉPARTEMENTS (`zones`), parce que l'annuaire public filtre sur un code postal. Le
 * back-office, lui, se pense en régions — « qui avons-nous en Bretagne ? ». Cette table
 * fait le chemin inverse, sans ajouter de champ en base ni d'appel à l'API.
 */

export interface Region {
  code: string
  nom: string
  departements: readonly string[]
}

export const REGIONS: readonly Region[] = [
  { code: 'ara', nom: 'Auvergne-Rhône-Alpes', departements: ['01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'] },
  { code: 'bfc', nom: 'Bourgogne-Franche-Comté', departements: ['21', '25', '39', '58', '70', '71', '89', '90'] },
  { code: 'bre', nom: 'Bretagne', departements: ['22', '29', '35', '56'] },
  { code: 'cvl', nom: 'Centre-Val de Loire', departements: ['18', '28', '36', '37', '41', '45'] },
  { code: 'cor', nom: 'Corse', departements: ['2A', '2B'] },
  { code: 'ges', nom: 'Grand Est', departements: ['08', '10', '51', '52', '54', '55', '57', '67', '68', '88'] },
  { code: 'hdf', nom: 'Hauts-de-France', departements: ['02', '59', '60', '62', '80'] },
  { code: 'idf', nom: 'Île-de-France', departements: ['75', '77', '78', '91', '92', '93', '94', '95'] },
  { code: 'nor', nom: 'Normandie', departements: ['14', '27', '50', '61', '76'] },
  { code: 'naq', nom: 'Nouvelle-Aquitaine', departements: ['16', '17', '19', '23', '24', '33', '40', '47', '64', '79', '86', '87'] },
  { code: 'occ', nom: 'Occitanie', departements: ['09', '11', '12', '30', '31', '32', '34', '46', '48', '65', '66', '81', '82'] },
  { code: 'pdl', nom: 'Pays de la Loire', departements: ['44', '49', '53', '72', '85'] },
  { code: 'pac', nom: "Provence-Alpes-Côte d'Azur", departements: ['04', '05', '06', '13', '83', '84'] },
]

/**
 * Le département d'une zone déclarée par un partenaire.
 *
 * Le champ `zones` est saisi en texte libre sur `/devenir-partenaire` : le seed y met des
 * numéros de département, mais une candidature peut tout aussi bien y écrire des codes
 * postaux à cinq chiffres (c'est le cas d'un partenaire de test resté en base). Les deux
 * doivent retomber sur le même département, sinon le partenaire disparaît de sa région.
 *
 * Même règle que `departement_du_code_postal` côté API, Corse comprise : le découpage réel
 * de la Corse est plus fin, on tranche au milieu faute de table officielle embarquée.
 */
function departementDeLaZone(zone: string): string {
  const code = zone.trim().toUpperCase()
  if (code.length <= 3) return code                    // « 13 », « 2A », « 974 »
  if (code.startsWith('20')) return code < '20200' ? '2A' : '2B'
  return code.slice(0, 2)
}

/** Les codes des régions qu'une liste de zones touche, dans l'ordre de `REGIONS`. */
export function regionsDesZones(zones: readonly string[] | null | undefined): string[] {
  if (!zones?.length) return []
  const couverts = new Set(zones.map(departementDeLaZone))
  return REGIONS.filter((r) => r.departements.some((d) => couverts.has(d))).map((r) => r.code)
}
