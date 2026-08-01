import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import SystemAdminDashboard from '../../components/system-admin/SystemAdminDashboard'
import SystemAdminSchoolsPage from '../../pages/system-admin/SystemAdminSchoolsPage'
import SystemAdminUsersPage from '../../pages/system-admin/SystemAdminUsersPage'
import SystemAdminAuditLogPage from '../../pages/system-admin/SystemAdminAuditLogPage'
import SystemAdminCataloguePage from '../../pages/system-admin/SystemAdminCataloguePage'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

const makeClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false } } })

function setSystemAdmin() {
  useAuthStore.setState({
    user: {
      id: 1,
      email: 'admin@test.com',
      first_name: 'Admin',
      last_name: 'User',
      role: 'system_admin' as any,
      county: null,
      is_email_verified: true,
    },
    isAuthenticated: true,
    isEmailVerified: true,
    isLoading: false,
  })
}

describe('SystemAdminDashboard', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSystemAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SystemAdminDashboard />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('renders stat cards with role labels', async () => {
    renderPage()
    expect(
      await screen.findByText('Learners', {}, { timeout: 5000 }),
    ).toBeTruthy()
    expect(screen.getByText('Counsellors')).toBeTruthy()
    expect(screen.getByText('Schools')).toBeTruthy()
    expect(screen.getByText('Parents')).toBeTruthy()
  })

  it('shows stat values from MSW data', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('45')).toBeTruthy()
      expect(screen.getByText('8')).toBeTruthy()
      expect(screen.getByText('11')).toBeTruthy()
      expect(screen.getByText('20')).toBeTruthy()
    })
  })

  it('shows Recent activity section', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Recent activity')).toBeTruthy()
    })
  })

  it('shows recent audit entries', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('School created')).toBeTruthy()
      expect(screen.getByText('Invite sent')).toBeTruthy()
    })
  })

  it('shows Create School button', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Create School')).toBeTruthy()
    })
  })

  it('shows View Audit Log button', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('View Audit Log')).toBeTruthy()
    })
  })

  it('shows Schools by County section', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Schools by County')).toBeTruthy()
    })
  })

  it('shows pilot health, assignment coverage and framework freshness', async () => {
    renderPage()

    expect(await screen.findByText('Verified learners')).toBeInTheDocument()
    expect(screen.getByText('Pending school links')).toBeInTheDocument()
    expect(screen.getByText('Assignment coverage')).toBeInTheDocument()
    expect(screen.getByText('Plans completed')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Current guidance framework' })).toBeInTheDocument()
    expect(screen.getByText('CBC-SS-PILOT-2026')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open official source' })).toHaveAttribute(
      'href',
      'https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf',
    )
  })
})

describe('SystemAdminCataloguePage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSystemAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SystemAdminCataloguePage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('shows framework provenance and active and inactive combinations', async () => {
    renderPage()

    expect(await screen.findByText('CBC Senior School Pilot Catalogue 2026')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open official source' })).toHaveAttribute(
      'href',
      'https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf',
    )
    expect(screen.getByText('Advanced Mathematics, Physics, Chemistry')).toBeInTheDocument()
    expect(screen.getByText('Biology, Chemistry, Agriculture')).toBeInTheDocument()
    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('filters combinations by search term', async () => {
    const user = userEvent.setup()
    renderPage()

    const search = await screen.findByRole('searchbox', {
      name: 'Search combinations',
    })
    await user.type(search, 'agriculture')

    expect(screen.getByText('Biology, Chemistry, Agriculture')).toBeInTheDocument()
    expect(screen.queryByText('Advanced Mathematics, Physics, Chemistry')).not.toBeInTheDocument()
  })

  it('deactivates a combination and exposes its impact before the action', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByText('2 active schools')).toBeInTheDocument()
    expect(screen.getByText('4 learner choices')).toBeInTheDocument()
    await user.click(screen.getByRole('button', {
      name: 'Deactivate Advanced Mathematics, Physics, Chemistry',
    }))

    await waitFor(() => {
      expect(screen.getAllByText('Inactive')).toHaveLength(2)
    })
  })
})

describe('SystemAdminSchoolsPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSystemAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SystemAdminSchoolsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('renders school list with school names', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Starehe Boys Centre')).toBeTruthy()
      expect(screen.getByText('Alliance Girls')).toBeTruthy()
    })
  })

  it('shows school codes', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('KIA001')).toBeTruthy()
      expect(screen.getByText('KIA002')).toBeTruthy()
    })
  })

  it('shows student and counselor counts', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('24')).toBeTruthy()
      expect(screen.getByText('30')).toBeTruthy()
    })
  })

  it('shows page heading', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Schools')).toBeTruthy()
    })
  })

  it('shows Create School button', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Create school' })).toBeTruthy()
    })
  })

  it('coordinates school records with view, overflow, details, and confirmed status actions', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Schools', level: 1 })).toBeInTheDocument()
    expect(await screen.findByRole('table', { name: 'Pilot schools' })).toBeInTheDocument()
    expect(screen.getByText('2 schools')).toHaveAttribute('aria-live', 'polite')

    await user.click(screen.getByRole('button', { name: 'View Starehe Boys Centre' }))
    expect(screen.getByRole('dialog', { name: 'Starehe Boys Centre details' })).toHaveTextContent('info@starehe.ac.ke')
    await user.click(screen.getByRole('button', { name: 'Close details' }))

    await user.click(screen.getByRole('button', { name: 'More actions for Starehe Boys Centre' }))
    expect(screen.getByRole('menuitem', { name: 'Edit' })).toBeInTheDocument()
    await user.click(screen.getByRole('menuitem', { name: 'Deactivate' }))
    expect(screen.getByRole('dialog', { name: 'Deactivate Starehe Boys Centre?' })).toBeInTheDocument()
  })
})

describe('SystemAdminUsersPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSystemAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SystemAdminUsersPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('renders user list with emails', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('jane@test.com')).toBeTruthy()
      expect(screen.getByText('bob@test.com')).toBeTruthy()
    })
  })

  it('shows user names', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Jane Doe')).toBeTruthy()
      expect(screen.getByText('Bob Smith')).toBeTruthy()
    })
  })

  it('shows role badges', async () => {
    renderPage()
    await waitFor(() => {
      // Role badges have specific class names; use getAllByText since filter dropdown also has these labels
      const studentBadges = screen.getAllByText('Student')
      expect(studentBadges.length).toBeGreaterThanOrEqual(2) // one in filter, one in table
      const counselorBadges = screen.getAllByText('Counsellor')
      expect(counselorBadges.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows page heading', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Users')).toBeTruthy()
    })
  })

  it('shows total user count', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('2 users')).toHaveAttribute('aria-live', 'polite')
    })
  })

  it('coordinates users with decision fields, details, overflow actions, and confirmation', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByRole('table', { name: 'Platform users' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Users', level: 1 })).toBeInTheDocument()
    expect(screen.getByText('2 users')).toHaveAttribute('aria-live', 'polite')

    await user.click(screen.getByRole('button', { name: 'View Jane Doe' }))
    expect(screen.getByRole('dialog', { name: 'Jane Doe details' })).toHaveTextContent('jane@test.com')
    expect(screen.getByRole('dialog', { name: 'Jane Doe details' })).toHaveTextContent('Starehe Boys')
    await user.click(screen.getByRole('button', { name: 'Close details' }))

    await user.click(screen.getByRole('button', { name: 'More actions for Jane Doe' }))
    expect(screen.getByRole('menuitem', { name: 'Download PDF' })).toBeInTheDocument()
    await user.click(screen.getByRole('menuitem', { name: 'Deactivate' }))
    expect(screen.getByRole('dialog', { name: 'Deactivate Jane Doe?' })).toBeInTheDocument()
  })
})

describe('SystemAdminAuditLogPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setSystemAdmin()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SystemAdminAuditLogPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('renders audit log entries with action labels', async () => {
    renderPage()
    await waitFor(() => {
      // Action labels appear in both filter dropdown and table badges, so use getAllByText
      const schoolCreated = screen.getAllByText('School created')
      expect(schoolCreated.length).toBeGreaterThanOrEqual(2) // one in filter, one in table
      const inviteSent = screen.getAllByText('Invite sent')
      expect(inviteSent.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows actor names', async () => {
    renderPage()
    await waitFor(() => {
      const actorCells = screen.getAllByText('Admin User')
      expect(actorCells.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('shows page heading', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Audit log', level: 1 })).toBeTruthy()
    })
  })

  it('shows total entry count', async () => {
    renderPage()
    await waitFor(() => {
      const header = screen.getByText('2 entries')
      expect(header).toBeTruthy()
    })
  })

  it('shows target info', async () => {
    renderPage()
    await waitFor(() => {
      // Target type and ID are rendered as separate text nodes in the <td>, so use a function matcher
      const cells = screen.getAllByRole('cell')
      const schoolTarget = cells.find(cell => cell.textContent?.includes('school') && cell.textContent?.includes('#1'))
      const userTarget = cells.find(cell => cell.textContent?.includes('user') && cell.textContent?.includes('#0'))
      expect(schoolTarget).toBeTruthy()
      expect(userTarget).toBeTruthy()
    })
  })

  it('keeps audit rows concise and opens structured metadata in a details drawer', async () => {
    const user = userEvent.setup()
    renderPage()

    const table = await screen.findByRole('table', { name: 'Audit log entries' })
    expect(table).toBeInTheDocument()
    expect(table.closest('.sysadmin-audit-page')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Audit log', level: 1 })).toBeInTheDocument()
    expect(screen.getByText('2 entries')).toHaveAttribute('aria-live', 'polite')
    expect(screen.queryByText(/\{"/)).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'View details for School created' }))
    const drawer = screen.getByRole('dialog', { name: 'School created details' })
    expect(drawer).toHaveTextContent('Starehe Boys')
    expect(drawer).toHaveTextContent('192.168.1.1')
  })
})
