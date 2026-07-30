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
    expect(await screen.findByRole('heading', { name: 'Karibu, Jane' })).toBeInTheDocument()
    expect(screen.getByText('Compare your saved combinations')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Continue' })).toHaveAttribute('href', '/compare')
    expect(screen.getByRole('heading', { name: 'Career insights' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Evidence to action' })).toBeInTheDocument()
    for (const stage of ['Evidence', 'Interests', 'Compare', 'Plan']) {
      expect(screen.getByText(stage)).toBeInTheDocument()
    }
    expect(screen.queryByRole('progressbar', { name: 'Career journey progress' })).not.toBeInTheDocument()
    expect(screen.getByText('Your strength shape')).toBeInTheDocument()
    expect(screen.getByText('Interest-aligned pathways')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Agreed next steps' })).toBeInTheDocument()
    expect(screen.getByText('Review your milestone dates.')).toBeInTheDocument()
    expect(screen.getByText(/suggestions are starting points for exploration/i)).toBeInTheDocument()
    expect(screen.queryByText('73%')).not.toBeInTheDocument()
  })

  it('renders CounselorDashboard for counselor role', async () => {
    setUser('counselor')
    render(<DashboardPage />, { wrapper })
    const hero = await screen.findByRole('region', { name: /Good .+, Jane/i })
    expect(hero).toHaveClass('db-hero--counsellor')
    expect(screen.getByLabelText(/Total students:/i)).toHaveClass('db-metric')
    expect(screen.getByLabelText(/Follow-ups due:/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Journeys reviewed:/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Priority queue' })).toBeInTheDocument()
    expect(screen.getByText('Academic evidence incomplete')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Recent interventions' })).toBeInTheDocument()
    expect(screen.getByText('Bring the latest mathematics evidence.')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Open full caseload' })[0]).toHaveAttribute(
      'href',
      '/counselor/students',
    )
    expect(screen.getAllByRole('link', { name: 'Manage interventions' })[0]).toHaveAttribute(
      'href',
      '/counselor/students',
    )
  })

  it('renders ParentDashboard for parent role', async () => {
    setUser('parent')
    render(<DashboardPage />, { wrapper })
    const hero = await screen.findByRole('region', { name: /Good .+, Jane/i })
    expect(hero).toHaveClass('db-hero--parent')
    expect(screen.getByRole('heading', { name: 'Learner support' })).toBeInTheDocument()
  })

  it('renders SchoolAdminDashboard for school_admin role', async () => {
    setUser('school_admin')
    render(<DashboardPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('Starehe Boys Centre')).toBeInTheDocument()
    })
  })
})
