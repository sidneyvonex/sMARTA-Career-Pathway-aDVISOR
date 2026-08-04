import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SchoolAdminDashboard from '../../components/dashboard/admin/SchoolAdminDashboard'
import CounselorDashboard from '../../components/dashboard/counselor/CounselorDashboard'
import SystemAdminDashboard from '../../components/system-admin/SystemAdminDashboard'
import { server } from '../msw/server'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

function renderDashboard(component: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{component}</MemoryRouter>
    </QueryClientProvider>,
  )
}

function pdfResponse() {
  return new HttpResponse('%PDF report', {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': 'attachment; filename="role-report.pdf"',
    },
  })
}

describe('role dashboard report actions', () => {
  beforeEach(() => {
    global.URL.createObjectURL = vi.fn(() => 'blob:role-report')
    global.URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  })

  it('forwards the school roster grade filter', async () => {
    let requestedGrade: string | null = null
    server.use(http.get('/api/v1/reports/school/roster/pdf/', ({ request }) => {
      requestedGrade = new URL(request.url).searchParams.get('grade')
      return pdfResponse()
    }))
    renderDashboard(<SchoolAdminDashboard />)
    await userEvent.selectOptions(await screen.findByLabelText('Roster grade'), '10')
    await userEvent.click(screen.getByRole('button', { name: /Download learner roster/i }))
    await waitFor(() => expect(requestedGrade).toBe('10'))
  })

  it('downloads the counsellor overview from the counsellor endpoint', async () => {
    let requested = false
    server.use(http.get('/api/v1/reports/counselor/overview/pdf/', () => {
      requested = true
      return pdfResponse()
    }))
    renderDashboard(<CounselorDashboard />)
    await userEvent.click(await screen.findByRole('button', { name: /Download caseload overview/i }))
    await waitFor(() => expect(requested).toBe(true))
  })

  it('downloads both system reports from their respective endpoints', async () => {
    const requested: string[] = []
    server.use(
      http.get('/api/v1/reports/system/overview/pdf/', () => {
        requested.push('overview')
        return pdfResponse()
      }),
      http.get('/api/v1/reports/system/schools/pdf/', () => {
        requested.push('schools')
        return pdfResponse()
      }),
    )
    renderDashboard(<SystemAdminDashboard />)
    await userEvent.click(await screen.findByRole('button', { name: /Download platform overview/i }))
    await waitFor(() => expect(requested).toContain('overview'))
    await userEvent.click(screen.getByRole('button', { name: /Download schools directory/i }))
    await waitFor(() => expect(requested).toContain('schools'))
  })
})
