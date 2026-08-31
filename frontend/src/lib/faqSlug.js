/**
 * Identifiant d'URL d'une fiche, dérivé de sa question.
 *
 * Ce fichier est volontairement en JavaScript simple : il est importé À LA FOIS par
 * l'application React (Vite/TypeScript) et par le script de pré-rendu (Node). Une seule
 * implémentation, donc aucun risque que les liens internes pointent vers des pages
 * qui n'auraient pas été générées.
 *
 * La fonction doit rester DÉTERMINISTE et STABLE : changer sa logique change toutes les
 * URL du site, et casse le référencement acquis. Ne la modifier qu'avec des redirections.
 *
 * @param {string} question
 * @returns {string}
 */
export function faqSlug(question) {
  return (question || '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // retire les accents
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')     // tout le reste devient un tiret
    .replace(/^-+|-+$/g, '')
    .slice(0, 70)
    .replace(/-+$/g, '')             // pas de tiret final après la troncature
}
