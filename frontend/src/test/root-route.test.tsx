import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'
import { useAuthStore } from '../store/authStore'

function renderApp() {
  return render(<App />)
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isEmailVerified: false, isLoading: true })
})

describe('RootRoute at /', () => {
  it('shows a loading state while auth is resolving', () => {
    renderApp()
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('shows the LandingPage hero when auth resolves logged out', () => {
    useAuthStore.setState({ isLoading: false, isAuthenticated: false })
    renderApp()
    expect(
      screen.getByRole('heading', { level: 1 })
    ).toHaveTextContent(/discover\.\s*plan\.\s*choose\.\s*succeed\./i)
    expect(screen.getAllByRole('link', { name: /get started/i }).length).toBeGreaterThan(0)
  })

  it('shows the Dashboard (not the landing hero) when authenticated', () => {
    useAuthStore.setState({
      isLoading: false,
      isAuthenticated: true,
      user: {
        id: 1,
        email: 'test@example.com',
        first_name: 'Jane',
        last_name: 'Doe',
        role: 'student' as any,
        county: 'kiambu',
        is_email_verified: true,
      },
      isEmailVerified: true,
    })
    renderApp()
    expect(screen.queryByRole('link', { name: /get started/i })).not.toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: /main navigation/i })).toBeInTheDocument()
  })

  it('sends an authenticated user to email verification until their address is verified', () => {
    useAuthStore.setState({
      isLoading: false,
      isAuthenticated: true,
      user: {
        id: 2,
        email: 'unverified@example.com',
        first_name: 'Amani',
        last_name: 'Otieno',
        role: 'student',
        county: 'kiambu',
        is_email_verified: false,
      },
      isEmailVerified: false,
    })

    renderApp()

    expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument()
    expect(screen.queryByRole('complementary', { name: /main navigation/i })).not.toBeInTheDocument()
  })
})
