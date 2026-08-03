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
    expect(screen.getByText(/Grade 9 · Kiambu · School-linked/)).toBeInTheDocument()
  })

  it('renders RIASEC scores', async () => {
    renderPage()
    expect(await screen.findByText(/Holland Code: RIA/)).toBeInTheDocument()
    expect(screen.getByLabelText('Realistic')).toBeInTheDocument()
  })

  it('renders career pathways', async () => {
    renderPage()
    expect(await screen.findByText('Engineering')).toBeInTheDocument()
    expect(screen.getByText('Strongest interest alignment')).toBeInTheDocument()
    expect(screen.queryByText('90%')).not.toBeInTheDocument()
    expect(screen.getByText('Medicine')).toBeInTheDocument()
    expect(screen.getByText(/starting points for discussion/i)).toBeInTheDocument()
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

  it('renders counselor note', async () => {
    renderPage()
    expect(await screen.findByText(/great progress in mathematics/i)).toBeInTheDocument()
  })

  it('renders evidence completeness, provisional choice, plan milestones and report', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Evidence completeness' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Academic readiness' })).not.toBeInTheDocument()
    expect(screen.getByText(/2 of 2 enrolled subjects have grade evidence/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Provisional combination' })).toBeInTheDocument()
    expect(screen.getByText('Agriculture, Biology & Chemistry')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Plan milestones' })).toBeInTheDocument()
    expect(screen.getByText('Review two pilot schools')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Parent-visible notes' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Agreed next steps' })).toBeInTheDocument()
    expect(screen.getByText('Discuss the reviewed learner plan.')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Download report' })).toHaveLength(2)
  })

  it('renders learner-approved progress and goals as read-only advisory context', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Academic progress' })).toBeInTheDocument()
    expect(screen.getByText('The latest evidence needs attention.')).toBeInTheDocument()
    expect(screen.getByText(/Academic progress is advisory only/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Academic targets' })).toBeInTheDocument()
    expect(screen.getByText('Read together three evenings each week.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Education goals' })).toBeInTheDocument()
    expect(screen.getByText('University of Nairobi')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Evidence used for this status' })).toBeInTheDocument()
    expect(screen.getAllByText('Learner entered').length).toBeGreaterThan(0)
    expect(screen.getByText('Verification removed; school provenance retained')).toBeInTheDocument()
    expect(screen.getByText(/PROGRAMME-CBE · 2026 exploration cycle/i)).toBeInTheDocument()
    expect(screen.getByText(/Historical reference only/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open programme source' })).toHaveAttribute(
      'href', 'https://programme.example/source',
    )
    expect(screen.queryByRole('button', { name: /edit.*goal/i })).not.toBeInTheDocument()
  })

  it('shows deliberate empty states when approved evidence is absent', async () => {
    const { server } = await import('./msw/server')
    const { http, HttpResponse } = await import('msw')
    server.use(
      http.get('/api/v1/parents/children/:id/', () => HttpResponse.json({
        data: {
          profile: {
            id: 12,
            first_name: 'Amina',
            last_name: 'Kamau',
            email: 'amina@example.com',
            county: 'kiambu',
            grade: 9,
            mode: 'self_guided',
            bio: '',
            date_of_birth: null,
            career_interests: '',
            photo_url: null,
          },
          subjects: [],
          assessment: null,
          evidence_completeness: {
            status: 'not_started',
            total_subjects: 0,
            subjects_with_evidence: 0,
            total_grade_records: 0,
          },
          provisional_combination: null,
          plan: null,
          counselor: null,
          latest_note: null,
          parent_visible_notes: [],
        },
        error: null,
        message: '',
      })),
    )
    renderPage('12')

    expect(await screen.findByText(/has not completed the career interest assessment/i)).toBeInTheDocument()
    expect(screen.getByText('No subjects have been enrolled yet.')).toBeInTheDocument()
    expect(screen.getByText('No provisional combination has been selected.')).toBeInTheDocument()
    expect(screen.getByText('No learner plan has been started yet.')).toBeInTheDocument()
    expect(screen.getByText('No notes have been shared with parents yet.')).toBeInTheDocument()
  })

  it('announces the loading state', () => {
    renderPage()
    expect(screen.getByRole('status', { name: 'Loading learner summary' })).toBeInTheDocument()
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
