import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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
  })

  it('shows the student count after loading', async () => {
    renderPage()
    expect(await screen.findByText(/2 students assigned/)).toBeInTheDocument()
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
