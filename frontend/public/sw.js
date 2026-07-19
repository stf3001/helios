// Service worker HELIOS — coquille minimale pour l'installabilité PWA + cache léger.
// Stratégie : network-first pour la navigation (contenu frais), cache des assets statiques.
const CACHE = 'helios-v1'
const SHELL = ['/', '/helios', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (e) => {
  const { request } = e
  if (request.method !== 'GET') return
  // Ne jamais mettre en cache les appels API (données dynamiques / streaming)
  if (new URL(request.url).pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    e.respondWith(fetch(request).catch(() => caches.match('/helios') || caches.match('/')))
    return
  }
  e.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).then((res) => {
      const copy = res.clone()
      caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {})
      return res
    }).catch(() => cached))
  )
})
