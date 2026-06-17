import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import DashboardPage from '../pages/DashboardPage'
import { useAuthStore } from '../store/authStore'

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

function setUser(role: string) {
  useAuthStore.setState({
    user: {
      id: 1,
      email: 'test@example.com',
      first_name: 'Jane',
      last_name: 'Doe',
      role: role as any,
      county: 'kiambu',
      is_email_verified: true,
    },
    isAuthenticated: true,
    isEmailVerified: true,
    isLoading: false,
  })
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isEmailVerified: false, isLoading: false })
})

describe('DashboardPage', () => {
  it('renders nothing when user is null', () => {
    const { container } = render(<DashboardPage />, { wrapper })
    expect(container).toBeEmptyDOMElement()
  })

  it('renders StudentDashboard for student role', async () => {
    setUser('student')
    render(<DashboardPage />, { wrapper })
    await waitFor(() => {
      expect(screen.queryByText(/Dashboard not yet available/i)).not.toBeInTheDocument()
    })
  })

  it('renders CounselorDashboard for counselor role', async () => {
    setUser('counselor')
    render(<DashboardPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByRole('region', { name: /Welcome banner/i })).toBeInTheDocument()
    })
  })

  it('renders ParentDashboard for parent role', async () => {
    setUser('parent')
    render(<DashboardPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByRole('region', { name: /Welcome banner/i })).toBeInTheDocument()
    })
  })

  it('renders fallback for unhandled role', () => {
    setUser('school_admin')
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/not yet available/i)).toBeInTheDocument()
  })
})
