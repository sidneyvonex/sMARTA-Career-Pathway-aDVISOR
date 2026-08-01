import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { useAuthStore } from '../store/authStore'
import { server } from './msw/server'
import SchoolAdminDashboard from '../components/dashboard/admin/SchoolAdminDashboard'
import SchoolProfilePage from '../pages/admin/SchoolProfilePage'
import CounselorManagementPage from '../pages/admin/CounselorManagementPage'
import SchoolStudentsPage from '../pages/admin/SchoolStudentsPage'
import SchoolOfferingsPage from '../pages/admin/SchoolOfferingsPage'

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

  it('shows approval, journey, workload and offerings readiness', async () => {
    renderPage()

    expect(await screen.findByText('Pending school links')).toBeInTheDocument()
    expect(screen.getByText('Evidence ready')).toBeInTheDocument()
    expect(screen.getByText('Choices saved')).toBeInTheDocument()
    expect(screen.getByText('Plans created')).toBeInTheDocument()
    expect(screen.getByText('Reviews completed')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Counsellor workload' })).toBeInTheDocument()
    expect(screen.getByText('Alice Wanjiku')).toBeInTheDocument()
    expect(screen.getByText('Offerings configured')).toBeInTheDocument()
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

  it('shows a retryable error when the school profile query fails', async () => {
    server.use(
      http.get('/api/v1/school-admin/school/', () => HttpResponse.json({}, { status: 500 })),
    )
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('school profile could not load')
    expect(screen.getByRole('button', { name: 'Retry school profile' })).toBeInTheDocument()
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
    expect(await screen.findByRole('heading', { name: 'Counsellors', level: 1 })).toBeInTheDocument()
    expect(await screen.findByText('2 counsellors')).toBeInTheDocument()
    expect(await screen.findByText('Alice Wanjiku')).toBeInTheDocument()
    expect(screen.getByText('Bob Ochieng')).toBeInTheDocument()
    const email = screen.getByText('alice@school.co.ke')
    expect(getComputedStyle(email).overflowWrap).toBe('anywhere')
    expect(screen.getByRole('button', { name: 'View workload for Alice Wanjiku' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'More actions for Alice Wanjiku' })).toBeInTheDocument()
  })

  it('shows add counselor form with email input', async () => {
    renderPage()
    expect(await screen.findByPlaceholderText('Counselor email address')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Counselor' })).toBeInTheDocument()
  })

  it('opens workload details from the visible primary action', async () => {
    renderPage()
    await screen.findByText('Alice Wanjiku')
    await userEvent.click(screen.getByRole('button', { name: 'View workload for Alice Wanjiku' }))
    expect(screen.getByRole('dialog', { name: 'Alice Wanjiku workload' })).toHaveTextContent('8 assigned learners')
  })

  it('removes a counsellor only after named confirmation', async () => {
    let removed = false
    server.use(
      http.post('/api/v1/school-admin/counselors/10/remove/', () => {
        removed = true
        return HttpResponse.json({ data: null, error: null, message: 'Counselor removed.' })
      }),
    )
    renderPage()
    await screen.findByText('Alice Wanjiku')

    await userEvent.click(screen.getByRole('button', { name: 'More actions for Alice Wanjiku' }))
    await userEvent.click(screen.getByRole('menuitem', { name: 'Remove' }))
    expect(screen.getByRole('dialog', { name: 'Remove Alice Wanjiku?' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Remove counsellor' }))
    await waitFor(() => expect(removed).toBe(true))
  })

  it('cancels counsellor removal without sending a request', async () => {
    let requestCount = 0
    server.use(
      http.post('/api/v1/school-admin/counselors/10/remove/', () => {
        requestCount += 1
        return HttpResponse.json({ data: null, error: null, message: 'Counselor removed.' })
      }),
    )
    renderPage()
    await screen.findByText('Alice Wanjiku')

    await userEvent.click(screen.getByRole('button', { name: 'More actions for Alice Wanjiku' }))
    await userEvent.click(screen.getByRole('menuitem', { name: 'Remove' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByRole('dialog', { name: 'Remove Alice Wanjiku?' })).not.toBeInTheDocument()
    expect(requestCount).toBe(0)
  })

  it('uses a responsive workload list that can be searched', async () => {
    renderPage()
    expect(await screen.findByRole('table', { name: 'School counsellors' })).toBeInTheDocument()

    await userEvent.type(screen.getByRole('searchbox', { name: 'Search counsellors' }), 'Bob')
    expect(screen.getByText('Bob Ochieng')).toBeInTheDocument()
    expect(screen.queryByText('Alice Wanjiku')).not.toBeInTheDocument()
  })

  it('shows a retryable error when the counsellor query fails', async () => {
    server.use(
      http.get('/api/v1/school-admin/counselors/', () => HttpResponse.json({}, { status: 500 })),
    )
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('counsellor list could not load')
    expect(screen.getByRole('button', { name: 'Retry counsellors' })).toBeInTheDocument()
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

  it('shows pending school-link requests and lets the administrator approve', async () => {
    let receivedDecision = ''
    server.use(
      http.put(
        '/api/v1/school-admin/membership-requests/:studentId/decision/',
        async ({ request }) => {
          const body = await request.json() as { decision: string }
          receivedDecision = body.decision
          return HttpResponse.json({
            data: { student_id: 22, school_membership_status: 'active' },
            error: null,
            message: 'Learner school link approved.',
          })
        },
      ),
    )
    renderPage()

    expect(await screen.findByRole('heading', { name: 'School-link approval requests' })).toBeInTheDocument()
    expect(screen.getByText('Mary Wanjiru')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Approve Mary Wanjiru' }))

    await waitFor(() => expect(receivedDecision).toBe('approve'))
  })

  it('bulk assigns only selected unassigned approved learners', async () => {
    let assignedIds: number[] = []
    server.use(
      http.post('/api/v1/school-admin/assignments/bulk/', async ({ request }) => {
        const body = await request.json() as { student_ids: number[] }
        assignedIds = body.student_ids
        return HttpResponse.json({
          data: { assigned_count: body.student_ids.length, counselor_id: 10, student_ids: body.student_ids },
          error: null,
          message: '1 learner assigned to Alice Wanjiku.',
        }, { status: 201 })
      }),
    )
    renderPage()

    expect(await screen.findByRole('table', { name: 'Approved school learners' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('checkbox', { name: 'Select Kevin Otieno' }))
    await userEvent.selectOptions(
      screen.getByLabelText('Counsellor for selected learners'),
      '10',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Assign 1 learner' }))

    await waitFor(() => expect(assignedIds).toEqual([21]))
  })

  it('shows a retryable error when the student query fails', async () => {
    server.use(
      http.get('/api/v1/school-admin/students/', () => HttpResponse.json({}, { status: 500 })),
    )
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('student list could not load')
    expect(screen.getByRole('button', { name: 'Retry students' })).toBeInTheDocument()
  })
})

describe('SchoolOfferingsPage', () => {
  it('groups the catalogue, shows three subjects and warns before removal', async () => {
    const qc = makeClient()
    setSchoolAdmin()
    let savedIds: number[] | null = null
    server.use(
      http.put('/api/v1/school-admin/offerings/', async ({ request }) => {
        const body = await request.json() as { combination_ids: number[] }
        savedIds = body.combination_ids
        return HttpResponse.json({
          data: {
            school: { id: 1, school_code: 'PILOT-KIA-001', name: 'Pilot School', county: 'kiambu' },
            combination_ids: body.combination_ids,
            offerings: [],
          },
          error: null,
          message: 'School offerings updated.',
        })
      }),
    )
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SchoolOfferingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(await screen.findByRole('heading', {
      name: 'School subject offerings',
      level: 1,
    })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'STEM' })).toBeInTheDocument()
    expect(screen.getByText('Pure Sciences')).toBeInTheDocument()
    expect(screen.getByText('Agriculture')).toBeInTheDocument()
    expect(screen.getByText('Biology')).toBeInTheDocument()
    expect(screen.getByText('Chemistry')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('checkbox', { name: 'Offer Agriculture, Biology & Chemistry' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Removing an offering can affect learners')
    await userEvent.click(screen.getByRole('button', { name: 'Save offering set' }))
    await waitFor(() => expect(savedIds).toEqual([]))
  })
})
