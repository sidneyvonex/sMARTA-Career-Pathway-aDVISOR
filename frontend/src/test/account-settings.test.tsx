import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'
import { server } from './msw/server'
import AccountSettingsPage from '../pages/AccountSettingsPage'

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), loading: vi.fn() },
}))

const makeClient = () => new QueryClient({ defaultOptions: { queries: { retry: false } } })

function setStudent() {
  useAuthStore.setState({
    user: {
      id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
      role: 'student' as any, county: 'kiambu', is_email_verified: true,
    },
    isAuthenticated: true, isEmailVerified: true, isLoading: false,
  })
}

describe('AccountSettingsPage', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = makeClient()
    setStudent()
  })

  afterEach(() => {
    qc.clear()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AccountSettingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('submits updated name', async () => {
    renderPage()
    const firstNameInput = await screen.findByLabelText('First name')
    await userEvent.clear(firstNameInput)
    await userEvent.type(firstNameInput, 'Amina')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith('Profile updated.'))
  })

  it('shows an error when current password is wrong', async () => {
    server.use(
      http.post('/api/v1/auth/me/password/', () => HttpResponse.json(
        { data: null, error: true, message: 'Current password is incorrect.' },
        { status: 400 },
      )),
    )
    renderPage()
    await userEvent.type(await screen.findByLabelText('Current password'), 'WrongPass1!')
    await userEvent.type(screen.getByLabelText('New password'), 'NewPass456!')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'NewPass456!')
    await userEvent.click(screen.getByRole('button', { name: 'Update password' }))
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Current password is incorrect.'))
  })

  it('blocks submit when new password confirmation does not match', async () => {
    renderPage()
    await userEvent.type(await screen.findByLabelText('Current password'), 'CorrectPass123!')
    await userEvent.type(screen.getByLabelText('New password'), 'NewPass456!')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'Mismatch1!')
    await userEvent.click(screen.getByRole('button', { name: 'Update password' }))
    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument()
  })
})
