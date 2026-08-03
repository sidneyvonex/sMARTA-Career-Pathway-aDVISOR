import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../App'
import { useAuthStore } from '../store/authStore'
import { server } from './msw/server'


const learner = {
  id: 1,
  email: 'jane@test.com',
  first_name: 'Jane',
  last_name: 'Doe',
  role: 'student' as const,
  county: 'kiambu',
  is_email_verified: true,
}


describe('education goals route rollout', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'true')
    window.history.pushState({}, '', '/education-goals')
    useAuthStore.setState({
      user: learner,
      isAuthenticated: true,
      isEmailVerified: true,
      isLoading: false,
    })
    server.use(http.get('/api/v1/auth/me/', () => HttpResponse.json({
      data: { user: learner }, error: null, message: '',
    })))
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    window.history.pushState({}, '', '/')
  })

  it('renders the learner education-goals workspace while the rollout is on', async () => {
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Plan education goals', level: 1 })).toBeInTheDocument()
  })

  it('keeps the education-goals route unavailable while the rollout is off', async () => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'false')

    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Plan education goals' })).not.toBeInTheDocument()
  })
})
