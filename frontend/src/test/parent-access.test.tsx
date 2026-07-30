import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import ParentAccessPage from '../pages/ParentAccessPage'
import { server } from './msw/server'

const pendingLink = {
  id: 4,
  parent_name: 'Mary Wanjiku',
  parent_email: 'mary@example.com',
  claimed_relationship: 'mother',
  relationship_label: 'Mother',
  status: 'pending_learner',
  learner_approved_at: null,
  revoked_at: null,
  created_at: '2026-07-30T10:00:00Z',
}

function renderAccess() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ParentAccessPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ParentAccessPage', () => {
  it('explains pilot verification and supports invitations', async () => {
    let invitedEmail = ''
    server.use(
      http.post('/api/v1/auth/invite-parent/', async ({ request }) => {
        const body = await request.json() as { parent_email: string }
        invitedEmail = body.parent_email
        return HttpResponse.json({ data: null, error: null, message: 'Invitation sent.' })
      }),
    )
    renderAccess()

    expect(await screen.findByRole('heading', { name: 'Control who can view your progress' })).toBeInTheDocument()
    expect(screen.getByText(/Legal guardian identity is not independently verified/i)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Parent or guardian email'), {
      target: { value: 'supporter@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send invitation' }))

    await waitFor(() => expect(invitedEmail).toBe('supporter@example.com'))
  })

  it('shows a claimed relationship and approves a pending request', async () => {
    let status = 'pending_learner'
    server.use(
      http.get('/api/v1/students/parent-access/', () => HttpResponse.json({
        data: [{ ...pendingLink, status }],
        error: null,
        message: '',
      })),
      http.put('/api/v1/students/parent-access/:id/approve/', () => {
        status = 'active'
        return HttpResponse.json({
          data: { ...pendingLink, status, learner_approved_at: '2026-07-30T12:00:00Z' },
          error: null,
          message: 'Parent access approved.',
        })
      }),
    )
    renderAccess()

    expect(await screen.findByText('Mary Wanjiku')).toBeInTheDocument()
    expect(screen.getByText('Claims to be: Mother')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Approve access' }))

    await waitFor(() => expect(status).toBe('active'))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Revoke access' })).toBeInTheDocument())
  })

  it('revokes an active parent link', async () => {
    let status = 'active'
    server.use(
      http.get('/api/v1/students/parent-access/', () => HttpResponse.json({
        data: [{ ...pendingLink, status }],
        error: null,
        message: '',
      })),
      http.put('/api/v1/students/parent-access/:id/revoke/', () => {
        status = 'revoked'
        return HttpResponse.json({
          data: { ...pendingLink, status, revoked_at: '2026-07-30T12:00:00Z' },
          error: null,
          message: 'Parent access revoked.',
        })
      }),
    )
    renderAccess()

    fireEvent.click(await screen.findByRole('button', { name: 'Revoke access' }))

    await waitFor(() => expect(status).toBe('revoked'))
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Revoked access' })).toBeInTheDocument())
  })
})
