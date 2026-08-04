import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Toaster } from 'react-hot-toast'
import { describe, expect, it } from 'vitest'

import LettersPage from '../pages/LettersPage'
import { server } from './msw/server'

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <LettersPage />
      <Toaster />
    </QueryClientProvider>,
  )
}

describe('LettersPage', () => {
  it('lists captured emails newest-first', async () => {
    renderPage()
    const items = await screen.findAllByRole('button', { name: /account|password/i })
    expect(items[0]).toHaveAccessibleName(/Verify your CBC Guidance account/i)
  })

  it('shows the selected email body with a clickable link', async () => {
    renderPage()
    const item = await screen.findByRole('button', { name: /Verify your CBC Guidance account/i })
    await userEvent.click(item)
    const link = await screen.findByRole('link', { name: /verify-email\?token=/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('/verify-email?token='))
  })

  it('clears the inbox and shows a toast', async () => {
    renderPage()
    await screen.findByRole('button', { name: /Verify your CBC Guidance account/i })

    // After clearing, the list is empty.
    server.use(
      http.get('/api/v1/dev/letters/', () =>
        HttpResponse.json({ data: [], error: null, message: '' }),
      ),
    )
    await userEvent.click(screen.getByRole('button', { name: /Clear inbox/i }))

    expect(await screen.findByText(/Inbox cleared\./i)).toBeInTheDocument()
    expect(await screen.findByText(/No emails captured yet/i)).toBeInTheDocument()
  })
})
