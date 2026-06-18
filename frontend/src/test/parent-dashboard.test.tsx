import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import ParentDashboard from '../components/dashboard/parent/ParentDashboard'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

function renderDashboard() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ParentDashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ParentDashboard', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'parent@test.com',
        first_name: 'Jane',
        last_name: 'Doe',
        role: 'parent',
        county: 'kiambu',
        is_email_verified: true,
      },
      isAuthenticated: true,
      isEmailVerified: true,
      isLoading: false,
    })
  })

  it('renders greeting with parent name', async () => {
    renderDashboard()
    expect(await screen.findByText(/Good .+, Jane/)).toBeInTheDocument()
  })

  it('renders both children from API (fixes #40)', async () => {
    renderDashboard()
    const links = await screen.findAllByRole('link', { name: /view profile/i })
    expect(links).toHaveLength(2)
    expect(screen.getByText(/Tom's career personality/)).toBeInTheDocument()
    expect(screen.getByText(/Alice's career personality/)).toBeInTheDocument()
  })

  it('shows child grade chips', async () => {
    renderDashboard()
    expect(await screen.findByText(/Grade 9/)).toBeInTheDocument()
    expect(await screen.findByText(/Grade 10/)).toBeInTheDocument()
  })

  it('shows link to each child detail', async () => {
    renderDashboard()
    const links = await screen.findAllByRole('link', { name: /view profile/i })
    expect(links).toHaveLength(2)
    expect(links[0]).toHaveAttribute('href', '/parent/child/10')
    expect(links[1]).toHaveAttribute('href', '/parent/child/11')
  })

  it('shows error state on API failure', async () => {
    const { server } = await import('./msw/server')
    const { http, HttpResponse } = await import('msw')
    server.use(
      http.get('/api/v1/parents/children/', () => {
        return HttpResponse.json(
          { data: null, error: true, message: 'Server error' },
          { status: 500 },
        )
      }),
    )
    renderDashboard()
    expect(await screen.findByText(/couldn't load/i)).toBeInTheDocument()
  })
})
