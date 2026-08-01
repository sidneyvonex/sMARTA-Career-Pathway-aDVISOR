import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
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
    expect(screen.getByRole('region', { name: /Good .+, Jane/ })).toHaveClass('db-hero--parent')
  })

  it('uses a child switcher for multiple approved learners', async () => {
    renderDashboard()
    const switcher = await screen.findByLabelText('Choose learner')
    expect(switcher).toHaveValue('10')
    expect(screen.getByText('Agriculture, Biology & Chemistry')).toBeInTheDocument()

    fireEvent.change(switcher, { target: { value: '11' } })

    expect(screen.getByText('Still exploring options')).toBeInTheDocument()
    expect(screen.getByText('Complete your interest assessment')).toBeInTheDocument()
  })

  it('shows child grade chips', async () => {
    renderDashboard()
    expect(await screen.findByText(/Grade 9/)).toBeInTheDocument()
  })

  it('shows action, plan, milestone, prompt and approved access without fit percentage', async () => {
    renderDashboard()
    expect(await screen.findByText('Review your plan and next milestone')).toBeInTheDocument()
    expect(screen.getByText('1 of 3 milestones')).toBeInTheDocument()
    expect(screen.getByText(/Review two pilot schools/)).toBeInTheDocument()
    expect(screen.getByText(/How can I support your next plan milestone/)).toBeInTheDocument()
    expect(screen.getAllByText(/Learner approved/).length).toBeGreaterThan(0)
    expect(screen.queryByText(/% fit/i)).not.toBeInTheDocument()
  })

  it('shows learner summary and report actions for the selected child', async () => {
    renderDashboard()
    const links = await screen.findAllByRole('link', { name: /learner summary|review your plan/i })
    expect(links.some((link) => link.getAttribute('href') === '/parent/child/10')).toBe(true)
    expect(screen.getByRole('button', { name: 'Download report' })).toBeInTheDocument()
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
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load/i)
  })

  it('explains that learner approval is required when no child is visible', async () => {
    const { server } = await import('./msw/server')
    const { http, HttpResponse } = await import('msw')
    server.use(
      http.get('/api/v1/parents/children/', () => HttpResponse.json({
        data: [],
        error: null,
        message: '',
      })),
    )

    renderDashboard()

    expect(await screen.findByRole('heading', { name: 'No learner access approved yet' })).toBeInTheDocument()
    expect(screen.getByText(/must approve access/i)).toBeInTheDocument()
    expect(screen.queryByText(/contact your school/i)).not.toBeInTheDocument()
  })
})
