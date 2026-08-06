import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute'
import { useAuthStore } from '../store/authStore'

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={['/private']}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/private" element={<p>Private dashboard content</p>} />
        </Route>
        <Route path="/login" element={<p>Login page</p>} />
        <Route path="/verify-email" element={<p>Email verification required</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isEmailVerified: false,
    isLoading: false,
  })
})

describe('ProtectedRoute', () => {
  it('redirects an unverified authenticated user to email verification', () => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'unverified@example.com',
        first_name: 'Amani',
        last_name: 'Otieno',
        role: 'student',
        county: 'kiambu',
        is_email_verified: false,
      },
      isAuthenticated: true,
      isEmailVerified: false,
      isLoading: false,
    })

    renderProtectedRoute()

    expect(screen.getByText('Email verification required')).toBeInTheDocument()
    expect(screen.queryByText('Private dashboard content')).not.toBeInTheDocument()
  })

  it('allows a verified authenticated user through', () => {
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'verified@example.com',
        first_name: 'Amani',
        last_name: 'Otieno',
        role: 'student',
        county: 'kiambu',
        is_email_verified: true,
      },
      isAuthenticated: true,
      isEmailVerified: true,
      isLoading: false,
    })

    renderProtectedRoute()

    expect(screen.getByText('Private dashboard content')).toBeInTheDocument()
  })
})
