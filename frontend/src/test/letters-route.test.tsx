import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '../App'
import { useAuthStore } from '../store/authStore'

describe('dev mailbox route gating', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    window.history.pushState({}, '', '/')
    useAuthStore.setState({ isLoading: false })
  })

  it('serves /letters in development mode', async () => {
    window.history.pushState({}, '', '/letters')
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Dev Mailbox' })).toBeInTheDocument()
  })

  it('does not serve /letters when not in dev mode', async () => {
    vi.stubEnv('DEV', false)
    window.history.pushState({}, '', '/letters')
    render(<App />)
    // Give the router a tick; the mailbox heading must never appear.
    await new Promise((r) => setTimeout(r, 0))
    expect(screen.queryByRole('heading', { name: 'Dev Mailbox' })).not.toBeInTheDocument()
  })
})
