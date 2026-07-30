import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import StudentListPage from '../pages/counselor/StudentListPage'
import StudentDetailPage from '../pages/counselor/StudentDetailPage'
import NotesListPage from '../pages/counselor/NotesListPage'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

const makeClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false } } })

function setUser(role: string) {
  useAuthStore.setState({
    user: {
      id: 1,
      email: 'counselor@test.com',
      first_name: 'Dr',
      last_name: 'Smith',
      role: role as any,
      county: 'kiambu',
      is_email_verified: true,
    },
    isAuthenticated: true,
    isEmailVerified: true,
    isLoading: false,
  })
}

describe('StudentListPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setUser('counselor')
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <StudentListPage />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders "My Students" heading', async () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /my students/i })).toBeInTheDocument()
  })

  it('renders student names from MSW data', async () => {
    renderPage()
    expect(await screen.findByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByText('Brian Kamau')).toBeInTheDocument()
  })

  it('shows filter buttons', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Needs attention' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Assessed' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Filter by attention reason' })).toBeInTheDocument()
  })

  it('filters the caseload by explicit attention reason', async () => {
    renderPage()
    expect(await screen.findByText('Jane Doe')).toBeInTheDocument()

    fireEvent.change(
      screen.getByRole('combobox', { name: 'Filter by attention reason' }),
      { target: { value: 'no_plan' } },
    )

    expect(screen.getByText('Brian Kamau')).toBeInTheDocument()
    expect(screen.queryByText('Jane Doe')).not.toBeInTheDocument()
  })

  it('shows the student count after loading', async () => {
    renderPage()
    expect(await screen.findByText(/2 students assigned/)).toBeInTheDocument()
  })

  it('shows ranked interest alignment without a fit percentage', async () => {
    renderPage()
    expect((await screen.findAllByText('Interest alignment')).length).toBeGreaterThan(0)
    expect(screen.queryByText(/fit percentage/i)).not.toBeInTheDocument()
    expect(screen.queryByText('73%')).not.toBeInTheDocument()
  })
})

describe('StudentDetailPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setUser('counselor')
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/counselor/students/5']}>
          <Routes>
            <Route path="/counselor/students/:id" element={<StudentDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders student name from MSW data', async () => {
    renderPage()
    expect(await screen.findByText('Jane Doe')).toBeInTheDocument()
  })

  it('shows RIASEC assessment section', async () => {
    renderPage()
    expect(await screen.findByText('RIASEC Assessment')).toBeInTheDocument()
  })

  it('shows the grades section', async () => {
    renderPage()
    expect(await screen.findByText('Grades')).toBeInTheDocument()
  })

  it('shows back link to student list', async () => {
    renderPage()
    expect(await screen.findByText(/back to students/i)).toBeInTheDocument()
  })

  it('shows evidence, choices, plan and the intervention workflow', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Attention reasons' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Evidence summary' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Saved and provisional choices' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Learner plan' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Intervention timeline' })).toBeInTheDocument()
    expect(screen.getByLabelText('Agreed next step')).toBeInTheDocument()
    expect(screen.getByLabelText('Follow-up date')).toBeInTheDocument()
    expect(screen.getByText('Bring the latest mathematics evidence.')).toBeInTheDocument()
  })
})

describe('NotesListPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setUser('counselor')
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <NotesListPage />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders "My Notes" heading', async () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /my notes/i })).toBeInTheDocument()
  })

  it('renders note content from MSW data', async () => {
    renderPage()
    expect(await screen.findByText('Great progress in math.')).toBeInTheDocument()
    expect(screen.getByText('Needs help with science.')).toBeInTheDocument()
  })

  it('shows note count after loading', async () => {
    renderPage()
    expect(await screen.findByText(/2 notes total/)).toBeInTheDocument()
  })

  it('shows search input', async () => {
    renderPage()
    expect(screen.getByRole('searchbox', { name: /search notes/i })).toBeInTheDocument()
  })
})
