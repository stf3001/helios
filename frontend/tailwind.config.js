/** @type {import('tailwindcss').Config} */

/* Les couleurs ne sont PAS ecrites ici : elles vivent dans `src/index.css`, sous forme
   de triplets de canaux (`--h-accent: 168 66 15`). Ce detour par une variable CSS a une
   raison precise : il garde les modificateurs d'opacite de Tailwind (`bg-primary/10`,
   `text-dark/80`), tres utilises dans le site, tout en laissant UN seul endroit ou la
   palette se change. Le `<alpha-value>` est remplace par Tailwind a la compilation. */
const t = (nom) => `rgb(var(${nom}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        /* --- Socle ------------------------------------------------------- */
        sable: t('--h-sable'),       // fond de page, ivoire chaud
        cream: t('--h-sable-2'),     // bandeaux, badges, sections en retrait
        bord: t('--h-bord'),         // la bordure 1px de toutes les surfaces
        ink: t('--h-ink'),           // encre bleu-vert : titres, cartes sombres
        dark: t('--h-ink'),          // texte courant (meme encre que les titres)
        /* --- Accents ----------------------------------------------------- */
        primary: t('--h-accent'),    // terracotta : boutons, liens, mots mis en valeur
        terra: t('--h-accent-fonce'),// le meme, assombri — etats survol/actif
        sun: t('--h-or'),            // or : reserve a l'icone de la carte sombre
        sky: t('--h-bleu'),          // icones vent et eau
        leaf: t('--h-vert'),         // icones terre, pastille « en ligne »

        /* Neutres rechauffes. Le site ecrit `text-gray-600` et `border-gray-200` dans
           une soixantaine de fichiers : les redefinir ici les accorde au fond ivoire
           d'un coup, plutot que de reecrire des centaines de classes. */
        gray: {
          50: '#FAF7F0',
          100: '#F1EADC',
          200: '#E2D8C6',  // = bord
          300: '#CDC2AE',
          400: '#6E6A63',  // assombri par rapport au gris Tailwind : lisible sur ivoire (4,8:1)
          500: '#5A686D',
          600: '#4A5A5F',  // = texte secondaire
          700: '#3C4B50',
          800: '#2A383D',
          900: '#1B2A2F',  // = encre
        },
      },
      fontFamily: {
        display: ['Instrument Serif', 'Georgia', 'Times New Roman', 'serif'],
        sans: ['Plus Jakarta Sans', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      borderRadius: {
        /* 12px pour les boutons (`rounded-xl`, deja la valeur de Tailwind),
           18px pour les cartes et la barre de question. */
        '2xl': '18px',
      },
      boxShadow: {
        /* Une seule ombre dans tout le site, portee par la barre de question. */
        question: '0 18px 50px rgba(27, 42, 47, 0.10)',
      },
      keyframes: {
        'slide-up': { '0%': { transform: 'translateY(12px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        'fade-in': { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
      },
      animation: {
        'slide-up': 'slide-up 0.4s ease-out both',
        'fade-in': 'fade-in 0.5s ease-out both',
      },
    },
  },
  plugins: [],
}
