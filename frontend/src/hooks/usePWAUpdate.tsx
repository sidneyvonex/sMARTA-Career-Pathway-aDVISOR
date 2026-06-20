import { useEffect } from 'react'
import { registerSW } from 'virtual:pwa-register'
import toast from 'react-hot-toast'

export function usePWAUpdate() {
  useEffect(() => {
    const updateSW = registerSW({
      onNeedRefresh() {
        toast(
          (t) => (
            <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              A new version is available.
              <button
                type="button"
                onClick={() => {
                  updateSW(true)
                  toast.dismiss(t.id)
                }}
                style={{
                  background: 'var(--color-primary)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  padding: 'var(--space-1) var(--space-3)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                }}
              >
                Refresh
              </button>
            </span>
          ),
          { duration: Infinity },
        )
      },
      onOfflineReady() {
        // silently ready — no toast needed
      },
    })
  }, [])
}
