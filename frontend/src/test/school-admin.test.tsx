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
    expect(screen.getByText('Learners')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Counsellors')).toBeInTheDocument()
  })

  it('shows manage buttons', async () => {
    renderPage()
    expect(await screen.findByText('Manage school profile')).toBeInTheDocument()
    expect(screen.getAllByText('Manage counsellors')).not.toHaveLength(0)
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
    const offeringsStatus = screen.getByText('Offerings configured')
    expect(offeringsStatus).toBeInTheDocument()
    expect(offeringsStatus.closest('.db-panel')).toHaveClass('school-offerings-panel')
  })

  it('shows an aggregated cohort progress graph with year and subject filters', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Cohort progress by term' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Stacked bar chart of cohort CBC bands by term' })).toBeInTheDocument()
    expect(screen.getByText('29')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Cohort subject'), 'MTH')
    expect(screen.getAllByText('18').length).toBeGreaterThan(1)
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
    expect(await screen.findByLabelText('School name')).toBeInTheDocument()
    expect(screen.getByLabelText('School code')).toBeInTheDocument()
    expect(screen.getByLabelText('Phone')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('shows upload logo button', async () => {
    renderPage()
    expect(await screen.findByText('Upload logo')).toBeInTheDocument()
  })

  it('populates form with MSW school data', async () => {
    renderPage()
    const nameInput = await screen.findByLabelText('School name')
    expect(nameInput).toHaveValue('Starehe Boys Centre')
    const codeInput = screen.getByLabelText('School code')
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
    // Long emails truncate on one line (with the full value in a title tooltip)
    // rather than breaking mid-domain.
    expect(getComputedStyle(email).textOverflow).toBe('ellipsis')
    expect(email).toHaveAttribute('title', 'alice@school.co.ke')
    expect(screen.getByRole('button', { name: 'View workload for Alice Wanjiku' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'More actions for Alice Wanjiku' })).toBeInTheDocument()
  })

  it('shows add counselor form with email input', async () => {
    renderPage()
    expect(await screen.findByPlaceholderText('Counsellor email address')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add counsellor' })).toBeInTheDocument()
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

  it('resets a counsellor password after confirmation', async () => {
    let resetCalled = false
    server.use(
      http.post('/api/v1/school-admin/counselors/10/reset-password/', () => {
        resetCalled = true
        return HttpResponse.json({ data: null, error: null, message: 'Password reset. New credentials sent to alice@school.co.ke.' })
      }),
    )
    renderPage()
    await screen.findByText('Alice Wanjiku')

    await userEvent.click(screen.getByRole('button', { name: 'More actions for Alice Wanjiku' }))
    await userEvent.click(screen.getByRole('menuitem', { name: 'Reset password' }))
    expect(screen.getByRole('dialog', { name: 'Reset password for Alice Wanjiku?' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() => expect(resetCalled).toBe(true))
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
    expect(await screen.findByRole('heading', { name: 'Learners', level: 1 })).toBeInTheDocument()
    expect(await screen.findByText('Jane Muthoni')).toBeInTheDocument()
    expect(screen.getByText('Kevin Otieno')).toBeInTheDocument()
  })

  it('imports a learner CSV and offers the one-time credentials download', async () => {
    let uploadReceived = false
    server.use(
      http.post('/api/v1/school-admin/students/import/', () => {
        uploadReceived = true
        return HttpResponse.json({
          data: {
            created_count: 1,
            linked_count: 1,
            already_linked_count: 0,
            error_count: 1,
            created: [{
              id: 44,
              first_name: 'Amina',
              last_name: 'Kamau',
              email: 'amina@school.test',
              grade: 9,
              temporary_password: 'SecurePass123',
            }],
            linked: [{
              id: 45,
              first_name: 'Brian',
              last_name: 'Otieno',
              email: 'brian@school.test',
              grade: 10,
            }],
            already_linked: [],
            errors: [{ row: 3, email: 'bad', message: 'email is invalid' }],
          },
          error: null,
          message: '1 learner account created.',
        }, { status: 201 })
      }),
    )
    renderPage()
    await screen.findByText('Jane Muthoni')

    const file = new File(
      ['first_name,last_name,email,grade\nAmina,Kamau,amina@school.test,9'],
      'learners.csv',
      { type: 'text/csv' },
    )
    await userEvent.upload(screen.getByLabelText('Learner CSV file'), file)
    await userEvent.click(screen.getByRole('button', { name: 'Import learners' }))

    await waitFor(() => expect(uploadReceived).toBe(true))
    expect(screen.getByText('2 learners added')).toBeInTheDocument()
    expect(screen.getByText(/1 new account created/)).toBeInTheDocument()
    expect(screen.getByText(/1 existing account linked/)).toBeInTheDocument()
    expect(screen.getByText(/Existing learners keep their current password/)).toBeInTheDocument()
    expect(screen.getByText('1 row skipped')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Download login credentials' })).toBeInTheDocument()
    await userEvent.click(screen.getByText('Review skipped rows'))
    expect(screen.getByText(/Row 3 \(bad\): email is invalid/)).toBeInTheDocument()
  })

  it('previews school marks before importing them', async () => {
    let marksRequestCount = 0
    server.use(
      http.post('/api/v1/school-admin/marks/import/', () => {
        marksRequestCount += 1
        const committed = marksRequestCount === 2
        return HttpResponse.json({
          data: {
            period: { id: 11, year: 2026, term: 1, state: 'entry_open', can_submit: true },
            row_count: 1,
            valid_count: 1,
            error_count: 0,
            rows: [],
            ...(committed ? { created_count: 1, replaced_count: 0 } : {}),
          },
          error: null,
          message: committed ? 'School marks imported and verified.' : 'Marks file checked.',
        }, { status: committed ? 201 : 200 })
      }),
    )
    renderPage()
    await screen.findByText('Jane Muthoni')

    expect(screen.getByRole('heading', { name: 'Upload school marks' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /Term 2 2026/ })).toBeDisabled()

    await userEvent.selectOptions(screen.getByLabelText('Academic period'), '11')
    const file = new File(
      ['student_email,subject_code,level,raw_score\njane@example.com,MAT9,ME1,72.5'],
      'marks.csv',
      { type: 'text/csv' },
    )
    await userEvent.upload(screen.getByLabelText('Marks CSV file'), file)
    await userEvent.click(screen.getByRole('button', { name: 'Preview marks' }))

    expect(await screen.findByText('1 valid row')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Import and verify marks' }))
    expect(await screen.findByText(/1 result created/)).toBeInTheDocument()
  })

  it('shows filter buttons', async () => {
    renderPage()
    await screen.findByText('Jane Muthoni')
    expect(screen.getByRole('searchbox', { name: 'Search learners' }).closest('.management-toolbar')).toBeInTheDocument()
    expect(screen.getByText('2 learners')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Assigned' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Unassigned' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Assessed' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pending Assessment' })).toBeInTheDocument()
  })

  it('shows assignment dropdowns', async () => {
    renderPage()
    await screen.findByText('Jane Muthoni')
    const selects = screen.getAllByLabelText(/Assign counsellor for/)
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

  it('enables school actions from an authoritative active membership despite stale profile status', async () => {
    server.use(
      http.get('/api/v1/school-admin/students/', () => HttpResponse.json({
        data: [{
          id: 20,
          first_name: 'Jane',
          last_name: 'Muthoni',
          email: 'jane@student.co.ke',
          grade: 9,
          photo_url: null,
          quiz_status: 'done',
          school_membership_status: 'not_applicable',
          school: { id: 1, name: 'Starehe Boys Centre' },
          counselor_id: null,
          counselor_name: null,
          membership: { id: 51, status: 'active', record_source: 'learner_request', requested_at: '2026-01-10T08:00:00Z', started_at: '2026-01-11T08:00:00Z', ended_at: null },
          transfer: { previous_membership_count: 0 },
          academic_evidence: [],
        }],
        error: null,
        message: '',
      })),
    )
    renderPage()

    expect(await screen.findByRole('checkbox', {
      name: 'Select Jane Muthoni',
    })).toBeEnabled()
    expect(screen.getByRole('combobox', {
      name: 'Assign counsellor for Jane Muthoni',
    })).toBeEnabled()
    expect(screen.getByRole('button', {
      name: 'Download report for Jane Muthoni',
    })).toBeEnabled()
    expect(screen.getByText('School approved')).toBeInTheDocument()
  })

  it('shows transfer-safe provenance and only valid verification controls', async () => {
    renderPage()

    expect(await screen.findByText('Transferred in · 1 previous membership')).toBeInTheDocument()
    expect(screen.getByText('Verified by Previous School')).toBeInTheDocument()
    expect(screen.getAllByText('CBC-JUNIOR-SCHOOL pilot-2026')).toHaveLength(2)
    expect(screen.queryByRole('button', { name: 'Remove verification for Mathematics Term 1' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Verify Mathematics Term 2' })).toBeInTheDocument()
  })

  it('labels retained school provenance as previously verified after removal', async () => {
    server.use(
      http.get('/api/v1/school-admin/students/', () => HttpResponse.json({
        data: [{
          id: 20,
          first_name: 'Jane',
          last_name: 'Muthoni',
          email: 'jane@student.co.ke',
          grade: 9,
          photo_url: null,
          quiz_status: 'done',
          school_membership_status: 'active',
          school: { id: 1, name: 'Starehe Boys Centre' },
          counselor_id: null,
          counselor_name: null,
          membership: { id: 51, status: 'active', record_source: 'learner_request', requested_at: '2026-01-10T08:00:00Z', started_at: '2026-01-11T08:00:00Z', ended_at: null },
          transfer: { previous_membership_count: 0 },
          academic_evidence: [{
            id: 301,
            continuity_code: 'MTH',
            subject_name: 'Mathematics',
            academic_grade: 9,
            term: 1,
            year: 2026,
            level: 'ME1',
            framework: { code: 'CBC-JUNIOR-SCHOOL', version: 'pilot-2026' },
            source: 'school',
            verified_school: { id: 9, name: 'Previous School' },
            verified_at: null,
            can_verify: true,
            can_remove_verification: false,
          }],
        }],
        error: null,
        message: '',
      })),
    )
    renderPage()

    expect(await screen.findByText(
      'Previously verified by Previous School; verification removed',
    )).toBeInTheDocument()
    expect(screen.queryByText('Verified by Previous School')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', {
      name: 'Verify Mathematics Term 1',
    })).not.toBeInTheDocument()
  })

  it('shows a retryable error when the student query fails', async () => {
    server.use(
      http.get('/api/v1/school-admin/students/', () => HttpResponse.json({}, { status: 500 })),
    )
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('learner list could not load')
    expect(screen.getByRole('button', { name: 'Retry learners' })).toBeInTheDocument()
  })
})

describe('SchoolOfferingsPage', () => {
  it('renders the catalogue as a bounded selectable management table', async () => {
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
    expect(await screen.findByRole('table', { name: 'School subject offerings catalogue' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Select' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Combination' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Pathway and track' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Subjects' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Availability' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Status' })).toBeInTheDocument()
    expect(screen.getByText('Pure Sciences')).toBeInTheDocument()
    expect(screen.getByText('Agriculture')).toBeInTheDocument()
    expect(screen.getByText('Biology')).toBeInTheDocument()
    expect(screen.getByText('Chemistry')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('checkbox', { name: 'Offer Agriculture, Biology & Chemistry' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Removing an offering can affect learners')
    expect(screen.getByText('1 pending removal')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Discard changes' })).toBeEnabled()
    await userEvent.click(screen.getByRole('button', { name: 'Save offering set' }))
    await waitFor(() => expect(savedIds).toEqual([]))
  })
})
