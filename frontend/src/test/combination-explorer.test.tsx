import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CombinationExplorerPage from '../pages/CombinationExplorerPage'


function renderExplorer() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CombinationExplorerPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}


describe('CombinationExplorerPage', () => {
  it('shows the source-dated catalogue, pilot filters and combination evidence', async () => {
    renderExplorer()

    expect(await screen.findByRole('heading', { name: 'Explore subject combinations' })).toBeInTheDocument()
    expect(await screen.findByText('CBC Senior School Pilot Catalogue 2026')).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'View official source' })).toHaveAttribute(
      'href',
      'https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf',
    )
    expect(screen.getByRole('option', { name: 'Kirinyaga' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Nyandarua' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'All verified schools' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Agriculture, Biology & Chemistry' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Pure Sciences' })).toBeInTheDocument()
    expect(screen.getByText('Agriculture')).toBeInTheDocument()
    expect(screen.getByText('No verified school offering recorded yet')).toBeInTheDocument()
  })

  it('saves a combination and updates the comparison count', async () => {
    const user = userEvent.setup()
    renderExplorer()

    await user.click(await screen.findByRole('button', { name: 'Save combination' }))

    expect(await screen.findByRole('button', { name: 'Saved for comparison' })).toBeDisabled()
    await waitFor(() => expect(screen.getByText('1 of 3')).toBeInTheDocument())
  })

  it('can clear a filter set that has no results', async () => {
    const user = userEvent.setup()
    renderExplorer()

    const search = await screen.findByRole('searchbox', { name: 'Search' })
    await user.type(search, 'science')
    expect(search).toHaveValue('science')

    await user.clear(search)
    expect(search).toHaveValue('')
  })
})
