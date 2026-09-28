/**
 * Pré-rendu des fiches de connaissances.
 *
 * POURQUOI : le site est une application monopage. Sans ce script, chaque adresse renvoie la
 * même coquille vide (2 134 octets, aucun titre H1) et les 184 fiches sont invisibles pour les
 * moteurs de recherche. Ici on génère un vrai fichier HTML par fiche, avec son titre, sa
 * description et son contenu — l'application React reprend la main dès qu'elle est chargée.
 *
 * CHOIX : lecture directe des sources `kb/*.md` plutôt que de l'API. Le contenu est dans le
 * dépôt, donc disponible au build, sans base de données ni serveur à démarrer. Le déploiement
 * reste un simple envoi de fichiers statiques.
 *
 * Lancé automatiquement après `vite build` (script `postbuild`).
 */
import { readFileSync, readdirSync, writeFileSync, mkdirSync, statSync } from 'node:fs'
import { join, resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { faqSlug } from '../src/lib/faqSlug.js'

const ICI = dirname(fileURLToPath(import.meta.url))
const RACINE_FRONT = resolve(ICI, '..')
const DOSSIER_KB = resolve(RACINE_FRONT, '../kb')
const DIST = resolve(RACINE_FRONT, 'dist')

const SITE = process.env.HELIOS_SITE_URL || 'https://helios.fr'

/**
 * Aucune source n'est exclue : toute fiche listée dans la FAQ doit avoir sa page.
 * Exclure une source créerait des liens « Ouvrir cette fiche » menant à une coquille vide
 * pour les moteurs — une incohérence qui coûte plus cher que les quelques pages économisées.
 */
const SOURCES_EXCLUES = new Set()

/**
 * Même expression que le parseur Python (`agents_engine._FAQ_RE`) : format `### Q:` / `meta` / `R:`.
 * Les deux doivent rester synchronisés — un écart ici produirait des pages absentes du site.
 */
const RE_FICHE = /^### Q:\s*(.+?)\s*\n`([^`]+)`\s*\nR:\s*([\s\S]+?)(?=\n### Q:|\n## |\n---|$)/gm

function lireMeta(brut) {
  const out = {}
  for (const part of brut.split('|')) {
    const i = part.indexOf(':')
    if (i === -1) continue
    const cle = part.slice(0, i).trim()
    const val = part.slice(i + 1).trim()
    out[cle] = cle === 'tags' ? val.split(',').map((t) => t.trim()).filter(Boolean) : val
  }
  return out
}

function lireFiches() {
  const fiches = []
  for (const fichier of readdirSync(DOSSIER_KB).filter((f) => f.endsWith('.md') && f !== 'README.md')) {
    const source = fichier.replace(/\.md$/, '')
    if (SOURCES_EXCLUES.has(source)) continue
    const texte = readFileSync(join(DOSSIER_KB, fichier), 'utf-8')
    for (const m of texte.matchAll(RE_FICHE)) {
      const question = m[1].trim()
      const reponse = m[3].trim()
      fiches.push({ question, reponse, source, meta: lireMeta(m[2]), slug: faqSlug(question) })
    }
  }
  return fiches
}

const echapper = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** Description : phrase(s) entière(s) sous ~155 caractères — on ne coupe pas un mot en deux. */
function description(reponse) {
  const plat = reponse.replace(/\s+/g, ' ').trim()
  if (plat.length <= 155) return plat
  const coupe = plat.slice(0, 155)
  const fin = Math.max(coupe.lastIndexOf('. '), coupe.lastIndexOf(', '), coupe.lastIndexOf(' '))
  return coupe.slice(0, fin > 80 ? fin : 155).trim() + '…'
}

const LIMITE_TITRE = 60 // au-delà, Google coupe le titre dans ses résultats
const SUFFIXE = ' — HELIOS'

/**
 * Titre affiché dans les résultats de recherche.
 *
 * Trois cas, dans cet ordre de préférence :
 *  1. la question tient avec la marque   -> « Question — HELIOS »
 *  2. la question seule tient            -> « Question » (la question prime sur la marque :
 *     mieux vaut perdre le suffixe que couper la phrase)
 *  3. sinon                              -> coupe sur une frontière de MOT, jamais en plein mot
 */
function titre(question) {
  if (question.length + SUFFIXE.length <= LIMITE_TITRE) return question + SUFFIXE
  if (question.length <= LIMITE_TITRE) return question
  const coupe = question.slice(0, LIMITE_TITRE - 1)
  const espace = coupe.lastIndexOf(' ')
  return (espace > 30 ? coupe.slice(0, espace) : coupe).replace(/[\s,;:–—-]+$/, '') + '…'
}

function pageHtml(coquille, fiche) {
  const url = `${SITE}/faq/${fiche.slug}`
  // `seo_titre` / `seo_desc` dans les métadonnées de la fiche permettent d'écrire à la main
  // le titre et la description des sujets à fort enjeu, sans toucher au texte de la question.
  // Absents, la génération automatique s'applique — les 184 fiches restent donc couvertes.
  const desc = fiche.meta.seo_desc || description(fiche.reponse)
  const titrePage = fiche.meta.seo_titre || titre(fiche.question)

  // Données structurées : c'est ce qui permet l'affichage enrichi dans les résultats de recherche.
  const jsonld = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: fiche.question,
        acceptedAnswer: { '@type': 'Answer', text: fiche.reponse },
      },
    ],
  }

  // Contenu visible sans JavaScript. React remplace ce bloc au montage : les robots (et les
  // connexions lentes) voient la réponse tout de suite, l'utilisateur voit l'application ensuite.
  const contenu = `
      <article>
        <h1>${echapper(fiche.question)}</h1>
        <p>${echapper(fiche.reponse)}</p>
        <p><a href="/faq">Toutes les questions fréquentes</a> · <a href="/">HELIOS</a></p>
      </article>`

  return coquille
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${echapper(titrePage)}</title>`)
    .replace(/<meta name="description" content="[^"]*"\s*\/?>/, `<meta name="description" content="${echapper(desc)}" />`)
    .replace(/<meta property="og:title" content="[^"]*"\s*\/?>/, `<meta property="og:title" content="${echapper(fiche.question)}" />`)
    .replace(/<meta property="og:description" content="[^"]*"\s*\/?>/, `<meta property="og:description" content="${echapper(desc)}" />`)
    .replace(/<meta name="twitter:title" content="[^"]*"\s*\/?>/, `<meta name="twitter:title" content="${echapper(fiche.question)}" />`)
    .replace(/<meta name="twitter:description" content="[^"]*"\s*\/?>/, `<meta name="twitter:description" content="${echapper(desc)}" />`)
    .replace('</head>', `  <link rel="canonical" href="${url}" />\n    <script type="application/ld+json">${JSON.stringify(jsonld)}</script>\n  </head>`)
    .replace('<div id="root"></div>', `<div id="root">${contenu}\n    </div>`)
}

/**
 * Pages publiques fixes. Volontairement énumérées à la main plutôt que déduites du routeur :
 * l'espace client, l'inscription et le back-office ne doivent JAMAIS entrer dans le plan de
 * site, et une liste explicite rend cette exclusion évidente et vérifiable.
 */
const PAGES_FIXES = [
  '/', '/comment-ca-marche', '/helios', '/faq', '/glossaire',
  '/simulateur-solaire', '/potentiel-hydrique',
  '/partenaires', '/devenir-partenaire',
  '/engagements', '/vision', '/colibri', '/qui-sommes-nous',
]

/** Pages chapeau (`/aides`, `/solaire`…) : contenu éditorial dans `src/data/piliers.json`,
 *  même source que les pages React — la version servie aux moteurs dit donc la même chose. */
const PILIERS = JSON.parse(readFileSync(resolve(RACINE_FRONT, 'src/data/piliers.json'), 'utf-8'))

/** Pages locales : production PVGIS RÉELLE par ville (écart x1,5 entre Lille et Marseille).
 *  C'est cette différence de contenu qui distingue une page locale légitime d'une page
 *  géographique dupliquée — ces dernières sont sanctionnées par les moteurs. */
const VILLES = JSON.parse(readFileSync(resolve(RACINE_FRONT, 'src/data/villes.json'), 'utf-8'))

function villeHtml(coquille, v) {
  const url = `${SITE}/solaire/${v.slug}`
  const titre = `Panneaux solaires à ${v.nom} : production réelle`
  const desc = `À ${v.nom}, une installation de 6 kWc produit environ ${v.prod_6kwc.toLocaleString('fr-FR')} kWh par an (données PVGIS). Ce que ça change pour votre projet.`
  const contenu = `
      <article>
        <h1>Panneaux solaires à ${echapper(v.nom)}</h1>
        <p>À ${echapper(v.nom)} (zone climatique ${v.zone}), une toiture plein sud inclinée à 30° produit
        environ ${v.prod_3kwc} kWh par an pour 3 kWc, ${v.prod_6kwc} kWh pour 6 kWc et ${v.prod_9kwc} kWh
        pour 9 kWc. Données PVGIS (Commission européenne).</p>
        <p><a href="/solaire">Le guide solaire</a> · <a href="/simulateur-solaire">Simuler ma toiture</a></p>
      </article>`
  return coquille
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${echapper(titre)}</title>`)
    .replace(/<meta name="description" content="[^"]*"\s*\/?>/, `<meta name="description" content="${echapper(desc)}" />`)
    .replace(/<meta property="og:title" content="[^"]*"\s*\/?>/, `<meta property="og:title" content="${echapper(titre)}" />`)
    .replace(/<meta property="og:description" content="[^"]*"\s*\/?>/, `<meta property="og:description" content="${echapper(desc)}" />`)
    .replace('</head>', `  <link rel="canonical" href="${url}" />
  </head>`)
    .replace('<div id="root"></div>', `<div id="root">${contenu}
    </div>`)
}

/**
 * Zones privées : exclues du plan de site ET du robots.txt.
 *
 * ATTENTION — `Disallow` fonctionne par PRÉFIXE : `/partenaire` bloquerait aussi
 * `/partenaires`, l'annuaire public. Le `$` (fin d'URL, reconnu par Google) restreint la
 * règle à l'adresse exacte. Vérifier ce piège à chaque ajout de règle.
 */
const ZONES_PRIVEES = [
  '/admin', '/espace', '/mon-espace',
  '/partenaire$',  // l'espace partenaire seul — surtout pas /partenaires
  '/connexion', '/inscription', '/verifier-email',
]

const jour = (chemin) => statSync(chemin).mtime.toISOString().slice(0, 10)

/** HTML statique d'une page chapeau : intro + sections visibles sans JavaScript. */
function pilierHtml(coquille, pilier) {
  const url = `${SITE}/${pilier.slug}`
  const contenu = `
      <article>
        <h1>${echapper(pilier.titre)}</h1>
        <p>${echapper(pilier.sousTitre)}</p>
        <p>${echapper(pilier.intro)}</p>
${pilier.sections.map((s) => `        <h2>${echapper(s.titre)}</h2>\n        <p>${echapper(s.contenu)}</p>`).join('\n')}
        <p><a href="/faq">Toutes les questions fréquentes</a> · <a href="/">HELIOS</a></p>
      </article>`

  return coquille
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${echapper(pilier.metaTitre)}</title>`)
    .replace(/<meta name="description" content="[^"]*"\s*\/?>/, `<meta name="description" content="${echapper(pilier.metaDesc)}" />`)
    .replace(/<meta property="og:title" content="[^"]*"\s*\/?>/, `<meta property="og:title" content="${echapper(pilier.titre)}" />`)
    .replace(/<meta property="og:description" content="[^"]*"\s*\/?>/, `<meta property="og:description" content="${echapper(pilier.metaDesc)}" />`)
    .replace(/<meta name="twitter:title" content="[^"]*"\s*\/?>/, `<meta name="twitter:title" content="${echapper(pilier.titre)}" />`)
    .replace(/<meta name="twitter:description" content="[^"]*"\s*\/?>/, `<meta name="twitter:description" content="${echapper(pilier.metaDesc)}" />`)
    .replace('</head>', `  <link rel="canonical" href="${url}" />\n  </head>`)
    .replace('<div id="root"></div>', `<div id="root">${contenu}\n    </div>`)
}

function ecrireSitemap(fiches) {
  const majKb = jour(DOSSIER_KB)
  const aujourdhui = new Date().toISOString().slice(0, 10)

  const urls = [
    ...PAGES_FIXES.map((p) => ({ loc: p, maj: aujourdhui })),
    ...PILIERS.map((p) => ({ loc: `/${p.slug}`, maj: aujourdhui })),
    ...VILLES.map((v) => ({ loc: `/solaire/${v.slug}`, maj: aujourdhui })),
    ...fiches.map((f) => ({ loc: `/faq/${f.slug}`, maj: majKb })),
  ]

  const xml =
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    urls
      .map((u) => `  <url>\n    <loc>${SITE}${u.loc}</loc>\n    <lastmod>${u.maj}</lastmod>\n  </url>`)
      .join('\n') +
    '\n</urlset>\n'

  writeFileSync(join(DIST, 'sitemap.xml'), xml, 'utf-8')
  return urls.length
}

function ecrireRobots() {
  const txt =
    'User-agent: *\n' +
    'Allow: /\n\n' +
    '# Espaces privés et parcours de compte : aucun intérêt en recherche,\n' +
    '# et rien qui doive apparaître dans les résultats.\n' +
    ZONES_PRIVEES.map((z) => `Disallow: ${z}`).join('\n') +
    `\n\nSitemap: ${SITE}/sitemap.xml\n`
  writeFileSync(join(DIST, 'robots.txt'), txt, 'utf-8')
}

function main() {
  const coquille = readFileSync(join(DIST, 'index.html'), 'utf-8')
  const fiches = lireFiches()

  // Une collision de slug écraserait silencieusement une fiche : on échoue bruyamment.
  const vus = new Map()
  const collisions = []
  for (const f of fiches) {
    if (vus.has(f.slug)) collisions.push([vus.get(f.slug), f.question])
    else vus.set(f.slug, f.question)
  }
  if (collisions.length) {
    console.error('\n[pré-rendu] ÉCHEC — identifiants d\'URL en double :')
    for (const [a, b] of collisions) console.error(`  « ${a} »\n  « ${b} »\n`)
    process.exit(1)
  }

  // Fichiers plats `faq/<slug>.html` plutôt que `faq/<slug>/index.html` : servis directement
  // par nginx via `try_files $uri $uri.html`, sans redirection vers une barre oblique finale.
  // L'adresse servie correspond alors exactement à la balise canonique.
  mkdirSync(join(DIST, 'faq'), { recursive: true })
  for (const fiche of fiches) {
    writeFileSync(join(DIST, 'faq', `${fiche.slug}.html`), pageHtml(coquille, fiche), 'utf-8')
  }

  // Pages chapeau : `/aides.html`, `/solaire.html`… servis par `try_files $uri $uri.html`.
  for (const pilier of PILIERS) {
    writeFileSync(join(DIST, `${pilier.slug}.html`), pilierHtml(coquille, pilier), 'utf-8')
  }

  mkdirSync(join(DIST, 'solaire'), { recursive: true })
  for (const v of VILLES) {
    writeFileSync(join(DIST, 'solaire', `${v.slug}.html`), villeHtml(coquille, v), 'utf-8')
  }

  const nbUrls = ecrireSitemap(fiches)
  ecrireRobots()

  const parSource = fiches.reduce((acc, f) => ({ ...acc, [f.source]: (acc[f.source] || 0) + 1 }), {})
  console.log(`[pré-rendu] ${fiches.length} fiches générées sous /faq/`)
  console.log('[pré-rendu] ' + Object.entries(parSource).map(([s, n]) => `${s}:${n}`).join(' '))
  console.log(`[pré-rendu] ${VILLES.length} pages locales sous /solaire/`)
  console.log(`[pré-rendu] ${PILIERS.length} pages chapeau : ${PILIERS.map((p) => '/' + p.slug).join(' ')}`)
  console.log(`[pré-rendu] sitemap.xml : ${nbUrls} URL (${PAGES_FIXES.length} pages + ${PILIERS.length} chapeaux + ${fiches.length} fiches)`)
  console.log(`[pré-rendu] robots.txt écrit · site déclaré : ${SITE}`)
}

main()
