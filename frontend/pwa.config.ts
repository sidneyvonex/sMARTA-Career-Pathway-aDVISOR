export interface PwaRuntimeRule {
  urlPattern: RegExp
  handler: 'CacheFirst' | 'NetworkOnly'
  options?: {
    cacheName: string
    expiration: {
      maxEntries: number
      maxAgeSeconds: number
    }
  }
}

export const PWA_CACHE_ID = 'smarta-shauri-v1'

export const PWA_RUNTIME_CACHING: PwaRuntimeRule[] = [
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
