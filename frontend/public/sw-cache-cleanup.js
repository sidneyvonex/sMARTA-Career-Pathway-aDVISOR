const LEGACY_PRIVATE_CACHE_NAMES = ['api-cache']

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all(LEGACY_PRIVATE_CACHE_NAMES.map((cacheName) => caches.delete(cacheName))),
  )
})
