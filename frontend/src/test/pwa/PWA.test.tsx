import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import InstallBanner from '../../components/InstallBanner'

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
