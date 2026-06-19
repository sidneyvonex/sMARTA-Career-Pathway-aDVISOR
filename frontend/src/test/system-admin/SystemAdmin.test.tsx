import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import SystemAdminDashboard from '../../components/system-admin/SystemAdminDashboard'
import SystemAdminSchoolsPage from '../../pages/system-admin/SystemAdminSchoolsPage'
import SystemAdminUsersPage from '../../pages/system-admin/SystemAdminUsersPage'
import SystemAdminAuditLogPage from '../../pages/system-admin/SystemAdminAuditLogPage'

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
    await waitFor(() => {
      expect(screen.getByText('Students')).toBeTruthy()
      expect(screen.getByText('Counselors')).toBeTruthy()
      expect(screen.getByText('Schools')).toBeTruthy()
      expect(screen.getByText('Parents')).toBeTruthy()
    })
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

  it('shows Recent Activity section', async () => {
    renderPage()
    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeTruthy()
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
      expect(screen.getByText('Create School')).toBeTruthy()
    })
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
      const counselorBadges = screen.getAllByText('Counselor')
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
      // The count text is split across text nodes due to JSX interpolation
      const header = screen.getByText((_, element) => {
        return element?.tagName === 'SPAN' && element?.textContent === '2 users total'
      })
      expect(header).toBeTruthy()
    })
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
      expect(screen.getByText('Audit Log')).toBeTruthy()
    })
  })

  it('shows total entry count', async () => {
    renderPage()
    await waitFor(() => {
      // The count text is split across text nodes due to JSX interpolation
      const header = screen.getByText((_, element) => {
        return element?.tagName === 'SPAN' && element?.textContent === '2 entries total'
      })
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
})
