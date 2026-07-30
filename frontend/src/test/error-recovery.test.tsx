import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import ErrorBoundary from '../components/common/ErrorBoundary'
import ErrorState from '../components/common/dashboard/ErrorState'

describe('frontend error recovery', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('catches unexpected render errors, logs context in development, and retries', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    let shouldThrow = true

    function UnstablePage() {
      if (shouldThrow) throw new Error('render failed')
      return <p>Recovered page</p>
    }

    render(
      <MemoryRouter>
        <ErrorBoundary>
          <UnstablePage />
        </ErrorBoundary>
      </MemoryRouter>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('This page could not continue')
    expect(consoleError).toHaveBeenCalledWith(
      '[Smarta Shauri] Unexpected frontend error',
      expect.objectContaining({
        error: expect.any(Error),
        componentStack: expect.any(String),
      }),
    )

    shouldThrow = false
    await userEvent.click(screen.getByRole('button', { name: 'Try this page again' }))
    expect(screen.getByText('Recovered page')).toBeInTheDocument()
  })

  it('offers reusable primary and safe-navigation recovery actions', async () => {
    const retry = vi.fn()
    render(
      <MemoryRouter>
        <ErrorState
          description="The learner list is temporarily unavailable."
          onRetry={retry}
          actionLabel="Reload learners"
          secondaryAction={{ label: 'Return to dashboard', to: '/' }}
        />
      </MemoryRouter>,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Reload learners' }))
    expect(retry).toHaveBeenCalledOnce()
    expect(screen.getByRole('link', { name: 'Return to dashboard' })).toHaveAttribute('href', '/')
  })
})
