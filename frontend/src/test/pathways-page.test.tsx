// frontend/src/test/pathways-page.test.tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import PathwaysPage from '../pages/PathwaysPage'

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><PathwaysPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

test('Pathways page shows all three current pathway names', async () => {
  renderPage()
  expect(
    screen.getByRole('heading', {
      level: 1,
      name: /STEM\. Social Sciences\. Arts & Sports\./i,
    }),
  ).toBeInTheDocument()
  expect(await screen.findByRole('heading', { name: 'STEM' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Social Sciences' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Arts & Sports Science' })).toBeInTheDocument()
})

test('Pathways page shows current tracks and source provenance', async () => {
  renderPage()

  expect(await screen.findByText('CBC-SS-PILOT-2026')).toBeInTheDocument()
  expect(screen.getAllByText('Pure Sciences').length).toBeGreaterThan(0)
  expect(screen.getAllByText('Applied Sciences').length).toBeGreaterThan(0)
  expect(screen.getByRole('link', { name: 'Open current official catalogue' })).toHaveAttribute(
    'href',
    'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
  )
  expect(screen.getAllByText(/five-county pilot/i).length).toBeGreaterThan(0)
  expect(screen.getByText(/what to explore next/i)).toBeInTheDocument()
  expect(screen.queryByText(/which one is yours/i)).not.toBeInTheDocument()
})
