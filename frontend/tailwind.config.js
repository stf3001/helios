/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#E8871E',   // orange solaire (Hydrolia: #43B0C1)
        sun: '#F5B700',
        terra: '#C05621',
        dark: '#1F2937',
      },
    },
  },
  plugins: [],
}
