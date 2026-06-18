import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import SchoolAdminDashboard from '../components/dashboard/admin/SchoolAdminDashboard'
import SchoolProfilePage from '../pages/admin/SchoolProfilePage'
import CounselorManagementPage from '../pages/admin/CounselorManagementPage'
import SchoolStudentsPage from '../pages/admin/SchoolStudentsPage'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

const makeClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false } } })

function setSchoolAdmin() {
  useAuthStore.setState({
    user: {
      id: 1,
      email: 'admin@starehe.ac.ke',
      first_name: 'Janet',
      last_name: 'Wambui',
      role: 'school_admin' as any,
      county: 'nairobi',
      is_email_verified: true,
    },
    isAuthenticated: true,
    isEmailVerified: true,
    isLoading: false,
  })
}

describe('SchoolAdminDashboard', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSchoolAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SchoolAdminDashboard />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders school name and stats from MSW data', async () => {
    renderPage()
    expect(await screen.findByText('Starehe Boys Centre')).toBeInTheDocument()
    expect(screen.getByText('24')).toBeInTheDocument()
    expect(screen.getByText('Students')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Counselors')).toBeInTheDocument()
  })

  it('shows manage buttons', async () => {
    renderPage()
    expect(await screen.findByText('Manage School Profile')).toBeInTheDocument()
    expect(screen.getByText('Manage Counselors')).toBeInTheDocument()
  })

  it('displays assessed and unassigned stat cards', async () => {
    renderPage()
    expect(await screen.findByText('18')).toBeInTheDocument()
    expect(screen.getByText('Assessed')).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
    expect(screen.getByText('Unassigned')).toBeInTheDocument()
  })
})

describe('SchoolProfilePage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSchoolAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SchoolProfilePage />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders school profile form with labels', async () => {
    renderPage()
    expect(await screen.findByLabelText('School Name')).toBeInTheDocument()
    expect(screen.getByLabelText('School Code')).toBeInTheDocument()
    expect(screen.getByLabelText('Phone')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('shows upload logo button', async () => {
    renderPage()
    expect(await screen.findByText('Upload Logo')).toBeInTheDocument()
  })

  it('populates form with MSW school data', async () => {
    renderPage()
    const nameInput = await screen.findByLabelText('School Name')
    expect(nameInput).toHaveValue('Starehe Boys Centre')
    const codeInput = screen.getByLabelText('School Code')
    expect(codeInput).toHaveValue('NAI001')
    expect(codeInput).toBeDisabled()
  })
})

describe('CounselorManagementPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSchoolAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <CounselorManagementPage />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders counselor list from MSW data', async () => {
    renderPage()
    expect(await screen.findByText('Alice Wanjiku')).toBeInTheDocument()
    expect(screen.getByText('Bob Ochieng')).toBeInTheDocument()
  })

  it('shows add counselor form with email input', async () => {
    renderPage()
    expect(await screen.findByPlaceholderText('Counselor email address')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Counselor' })).toBeInTheDocument()
  })

  it('shows remove buttons for each counselor', async () => {
    renderPage()
    await screen.findByText('Alice Wanjiku')
    const removeButtons = screen.getAllByRole('button', { name: 'Remove' })
    expect(removeButtons.length).toBe(2)
  })
})

describe('SchoolStudentsPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSchoolAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SchoolStudentsPage />
        </MemoryRouter>
      </QueryClientProvider>
    )
  }

  it('renders student list from MSW data', async () => {
    renderPage()
    expect(await screen.findByText('Jane Muthoni')).toBeInTheDocument()
    expect(screen.getByText('Kevin Otieno')).toBeInTheDocument()
  })

  it('shows filter buttons', async () => {
    renderPage()
    await screen.findByText('Jane Muthoni')
    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Assigned' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Unassigned' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Assessed' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pending Assessment' })).toBeInTheDocument()
  })

  it('shows assignment dropdowns', async () => {
    renderPage()
    await screen.findByText('Jane Muthoni')
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBe(2)
  })
})
