import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Port fixe : sans cela Vite glisse sur le port suivant s'il est occupe, et Helios prenait
    // alors celui d'Eolia (5174). Hydrolia est sur 5175.
    port: 5173,
    strictPort: true,
    proxy: { '/api': 'http://localhost:8000' },
  },
})
