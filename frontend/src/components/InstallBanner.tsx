import { useState, useEffect } from 'react'
import { useInstallPrompt } from '../hooks/useInstallPrompt'

export default function InstallBanner() {
  const { canInstall, promptInstall } = useInstallPrompt()
  const [dismissed, setDismissed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    setIsMobile(window.matchMedia('(max-width: 768px)').matches)
  }, [])

  useEffect(() => {
    const wasDismissed = sessionStorage.getItem('install-banner-dismissed')
    if (wasDismissed) setDismissed(true)
  }, [])

  if (!canInstall || dismissed || !isMobile) return null

  const handleDismiss = () => {
    setDismissed(true)
    sessionStorage.setItem('install-banner-dismissed', 'true')
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: 'var(--color-primary)',
        color: '#fff',
        padding: 'var(--space-3) var(--space-4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 'var(--space-3)',
        zIndex: 1000,
        fontSize: 'var(--font-size-sm)',
      }}
      role="banner"
      aria-label="Install app prompt"
    >
      <span>Install Smarta Shauri for quick access</span>
      <div style={{ display: 'flex', gap: 'var(--space-2)', flexShrink: 0 }}>
        <button
          type="button"
          onClick={promptInstall}
          style={{
            background: '#fff',
            color: 'var(--color-primary)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            padding: 'var(--space-1) var(--space-3)',
            fontWeight: 600,
            cursor: 'pointer',
            minHeight: 'var(--min-touch-target)',
          }}
        >
          Install
        </button>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Dismiss install prompt"
          style={{
            background: 'transparent',
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            fontSize: 'var(--font-size-lg)',
            padding: 'var(--space-1)',
            minHeight: 'var(--min-touch-target)',
            minWidth: 'var(--min-touch-target)',
          }}
        >
          ×
        </button>
      </div>
    </div>
  )
}
