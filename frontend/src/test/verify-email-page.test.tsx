import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import VerifyEmailPage from '../pages/VerifyEmailPage'
import { useAuthStore } from '../store/authStore'

const mocks = vi.hoisted(() => ({
  resendVerification: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  authApi: {
    resendVerification: mocks.resendVerification,
    verifyEmail: vi.fn(),
  },
}))

vi.mock('react-hot-toast', () => ({
  default: {
    success: mocks.toastSuccess,
    error: mocks.toastError,
  },
}))

beforeEach(() => {
  mocks.resendVerification.mockReset().mockResolvedValue({})
  mocks.toastSuccess.mockReset()
  mocks.toastError.mockReset()
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isEmailVerified: false,
    isLoading: false,
  })
})

describe('VerifyEmailPage', () => {
  it('resends to the email carried over from registration without requiring a session', async () => {
    render(
      <MemoryRouter
        initialEntries={[{
          pathname: '/verify-email',
          state: { email: 'student@example.com' },
        }]}
      >
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByLabelText(/email address/i)).toHaveValue('student@example.com')
    await userEvent.click(screen.getByRole('button', { name: /resend email/i }))

    await waitFor(() => {
      expect(mocks.resendVerification).toHaveBeenCalledWith('student@example.com')
    })
    expect(mocks.toastSuccess).toHaveBeenCalled()
  })
})
