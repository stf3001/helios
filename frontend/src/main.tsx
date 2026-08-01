import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)

// PWA : enregistre le service worker UNIQUEMENT en production (sinon il sert des assets
// périmés en dev et casse le HMR de Vite). Installable « Ajouter à l'écran d'accueil ».
if ('serviceWorker' in navigator) {
  if (import.meta.env.PROD) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {})
    })
  } else {
    // En DEV : purge tout service worker resté actif d'un ancien build de prod lancé sur le
    // même localhost — sinon il intercepte les requêtes et sert des assets périmés/cassés
    // (ex. une image mise en cache pendant un redémarrage de serveur). Auto-réparateur.
    navigator.serviceWorker.getRegistrations().then((regs) => regs.forEach((r) => r.unregister()))
    if ('caches' in window) caches.keys().then((keys) => keys.forEach((k) => caches.delete(k)))
  }
}
