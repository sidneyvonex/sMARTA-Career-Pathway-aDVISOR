import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import GradesPage from '../pages/GradesPage'
import { server } from './msw/server'

describe('GradesPage recovery', () => {
  it('shows a retryable error when required grade data cannot load', async () => {
    server.use(
      http.get('/api/v1/students/my-subjects/', () => HttpResponse.json({}, { status: 500 })),
    )
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })

    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <GradesPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(await screen.findByRole('alert')).toHaveTextContent('subjects and grades could not load')
    expect(screen.getByRole('button', { name: 'Retry grade data' })).toBeInTheDocument()
  })
})
