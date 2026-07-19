/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#E8871E',   // orange solaire — couleur dominante
        sun: '#F5B700',        // jaune soleil (accent chaud, logo)
        terra: '#C05621',      // orange terre
        ink: '#1D3F63',        // bleu marine (logo) — titres, confiance
        sky: '#2E86C1',        // bleu clair (logo) — accents froids
        leaf: '#57A64A',       // vert (logo) — énergie / éco
        cream: '#FDF8F3',      // fond chaleureux (remplace le gris froid)
        dark: '#1F2937',
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],   // titres — chaleureux, humain
        sans: ['Nunito', 'system-ui', 'sans-serif'], // corps — rond, lisible
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
