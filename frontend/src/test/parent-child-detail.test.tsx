import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import ChildDetailPage from '../pages/parent/ChildDetailPage'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

function renderPage(id = '10') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/parent/child/${id}`]}>
        <Routes>
          <Route path="/parent/child/:id" element={<ChildDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ChildDetailPage', () => {
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

  it('renders child name and grade', async () => {
    renderPage()
    expect(await screen.findByText(/Tom Doe/)).toBeInTheDocument()
    expect(screen.getByText(/Grade 9/)).toBeInTheDocument()
  })

  it('renders RIASEC scores', async () => {
    renderPage()
    expect(await screen.findByText(/Holland Code: RIA/)).toBeInTheDocument()
    expect(screen.getByLabelText('Realistic')).toBeInTheDocument()
  })

  it('renders career pathways', async () => {
    renderPage()
    expect(await screen.findByText('Engineering')).toBeInTheDocument()
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.getByText('Medicine')).toBeInTheDocument()
  })

  it('renders subjects with grade badges', async () => {
    renderPage()
    expect(await screen.findByText('Mathematics')).toBeInTheDocument()
    expect(screen.getByText('T1: ME1')).toBeInTheDocument()
    expect(screen.getByText('T2: EE1')).toBeInTheDocument()
  })

  it('renders counselor info', async () => {
    renderPage()
    expect(await screen.findByText(/Dr Smith/)).toBeInTheDocument()
    expect(screen.getByText('drsmith@school.com')).toBeInTheDocument()
  })

  it('has back link to dashboard', async () => {
    renderPage()
    const back = await screen.findByLabelText('Back to dashboard')
    expect(back).toHaveAttribute('href', '/')
  })

  it('shows error state on API failure', async () => {
    const { server } = await import('./msw/server')
    const { http, HttpResponse } = await import('msw')
    server.use(
      http.get('/api/v1/parents/children/:id/', () => {
        return HttpResponse.json(
          { data: null, error: true, message: 'Not found' },
          { status: 404 },
        )
      }),
    )
    renderPage('999')
    expect(await screen.findByText(/couldn't load profile/i)).toBeInTheDocument()
  })
})
