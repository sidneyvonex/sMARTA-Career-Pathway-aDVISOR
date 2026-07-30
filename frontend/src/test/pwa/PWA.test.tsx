import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import InstallBanner from '../../components/InstallBanner'
import { PWA_RUNTIME_CACHING } from '../../../pwa.config'
import { clearUserScopedStorage } from '../../lib/sessionCleanup'

vi.mock('../../hooks/useInstallPrompt', () => ({
  useInstallPrompt: vi.fn(),
}))

import { useInstallPrompt } from '../../hooks/useInstallPrompt'
const mockUseInstallPrompt = vi.mocked(useInstallPrompt)

describe('InstallBanner', () => {
  beforeEach(() => {
    sessionStorage.clear()
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockReturnValue({ matches: true }),
    })
  })

  it('renders when canInstall is true on mobile', () => {
    mockUseInstallPrompt.mockReturnValue({ canInstall: true, promptInstall: vi.fn() })
    render(<InstallBanner />)
    expect(screen.getByText('Install Smarta Shauri for quick access')).toBeInTheDocument()
  })

  it('does not render when canInstall is false', () => {
    mockUseInstallPrompt.mockReturnValue({ canInstall: false, promptInstall: vi.fn() })
    render(<InstallBanner />)
    expect(screen.queryByText('Install Smarta Shauri for quick access')).not.toBeInTheDocument()
  })

  it('does not render on desktop', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockReturnValue({ matches: false }),
    })
    mockUseInstallPrompt.mockReturnValue({ canInstall: true, promptInstall: vi.fn() })
    render(<InstallBanner />)
    expect(screen.queryByText('Install Smarta Shauri for quick access')).not.toBeInTheDocument()
  })

  it('calls promptInstall when Install is clicked', () => {
    const promptInstall = vi.fn()
    mockUseInstallPrompt.mockReturnValue({ canInstall: true, promptInstall })
    render(<InstallBanner />)
    fireEvent.click(screen.getByText('Install'))
    expect(promptInstall).toHaveBeenCalledOnce()
  })

  it('dismisses and sets sessionStorage when X is clicked', () => {
    mockUseInstallPrompt.mockReturnValue({ canInstall: true, promptInstall: vi.fn() })
    render(<InstallBanner />)
    fireEvent.click(screen.getByLabelText('Dismiss install prompt'))
    expect(screen.queryByText('Install Smarta Shauri for quick access')).not.toBeInTheDocument()
    expect(sessionStorage.getItem('install-banner-dismissed')).toBe('true')
  })
})

describe('PWA cache safety', () => {
  it.each([
    'https://smarta-shauri.test/api/v1/students/profile/',
    'https://smarta-shauri.test/api/v1/parents/children/',
    'https://smarta-shauri.test/api/v1/profile/photo.png',
  ])('does not runtime-cache authenticated route %s', (url) => {
    const matchingCacheRules = PWA_RUNTIME_CACHING.filter((rule) => (
      rule.handler !== 'NetworkOnly' && rule.urlPattern.test(url)
    ))
    expect(matchingCacheRules).toEqual([])
  })

  it('retains versioned runtime caching for non-API images', () => {
    const publicImageUrl = 'https://smarta-shauri.test/assets/pathway.webp'
    const matchingRule = PWA_RUNTIME_CACHING.find((rule) => rule.urlPattern.test(publicImageUrl))
    expect(matchingRule?.handler).toBe('CacheFirst')
    expect(matchingRule?.options?.cacheName).toBe('smarta-shauri-images-v1')
  })
})

describe('logout storage cleanup', () => {
  it('removes learner drafts without clearing unrelated browser preferences', () => {
    localStorage.setItem('riasec_draft', '{"1":4}')
    localStorage.setItem('theme-preference', 'dark')

    clearUserScopedStorage()

    expect(localStorage.getItem('riasec_draft')).toBeNull()
    expect(localStorage.getItem('theme-preference')).toBe('dark')
  })
})
