export interface PwaRuntimeRule {
  urlPattern: RegExp
  handler: 'CacheFirst' | 'NetworkFirst' | 'NetworkOnly'
  options?: {
    cacheName: string
    networkTimeoutSeconds?: number
    cacheableResponse?: {
      statuses: number[]
    }
    expiration: {
      maxEntries: number
      maxAgeSeconds: number
    }
  }
}

export const PWA_CACHE_ID = 'smarta-shauri-v1'

export const PWA_RUNTIME_CACHING: PwaRuntimeRule[] = [
  {
    // This endpoint is explicitly public and its payload carries the framework code.
    // Network-first refreshes that version while retaining one safe offline fallback.
    urlPattern: /^https?:\/\/[^/]+\/api\/v1\/guidance\/framework\/current\/?(?:\?.*)?$/i,
    handler: 'NetworkFirst',
    options: {
      cacheName: 'smarta-shauri-public-framework-v1',
      networkTimeoutSeconds: 4,
      cacheableResponse: {
        statuses: [200],
      },
      expiration: {
        maxEntries: 1,
        maxAgeSeconds: 60 * 60 * 24 * 7,
      },
    },
  },
  {
    // Keep every /api/ response on the network, including image-shaped URLs.
    urlPattern: /^https?:\/\/[^/]+\/(?!api\/).*\.(png|jpg|jpeg|svg|gif|webp)$/i,
    handler: 'CacheFirst',
    options: {
      cacheName: 'smarta-shauri-images-v1',
      expiration: {
        maxEntries: 100,
        maxAgeSeconds: 60 * 60 * 24 * 30,
      },
    },
  },
]
