import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { describe, expect, it } from 'vitest'

import EducationGoalsPage from '../pages/EducationGoalsPage'
import { institutionFixture, programmeFixture } from './msw/handlers'
import { server } from './msw/server'


function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <EducationGoalsPage />
        <Toaster />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}


async function selectInstitution(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button', { name: 'Explore University of Nairobi' }))
}


async function selectProgramme(user: ReturnType<typeof userEvent.setup>) {
  await selectInstitution(user)
  await user.click(await screen.findByRole('button', { name: 'View BSc Computer Science' }))
}


describe('education goals workspace', () => {
  it('shows sourced historical programme detail and the unavailable official-criteria explanation', async () => {
    const user = userEvent.setup()
    renderPage()

    await selectProgramme(user)

    const detail = await screen.findByRole('region', { name: 'BSc Computer Science details' })
    expect(within(detail).getByText('Historical reference')).toBeInTheDocument()
    expect(within(detail).getByText('Framework: KCSE')).toBeInTheDocument()
    expect(within(detail).getByText('Admission cycle: 2025/2026')).toBeInTheDocument()
    expect(within(detail).getByText('Effective date: 1 March 2025')).toBeInTheDocument()
    expect(within(detail).getByRole('link', { name: 'Open official source' })).toHaveAttribute(
      'href', 'https://students.kuccps.net/',
    )
    expect(within(detail).getByText('Verification: Historical')).toBeInTheDocument()
    expect(within(detail).getByText('Historical requirement')).toBeInTheDocument()
    expect(within(detail).getByText('Exploratory alignment')).toBeInTheDocument()
    expect(within(detail).getByText('Mathematics')).toBeInTheDocument()
    const subjectReference = within(detail).getByRole('article', { name: 'Mathematics subject reference' })
    expect(subjectReference).toHaveTextContent('KCSE · 2025/2026 · Effective 1 March 2025 · Verification: Historical')
    expect(within(subjectReference).getByRole('link', { name: 'Open Mathematics source' })).toHaveAttribute(
      'href', 'https://students.kuccps.net/',
    )
    const historicalReference = within(detail).getByRole('article', { name: 'Historical admission reference' })
    expect(historicalReference).toHaveTextContent('Reference only')
    expect(historicalReference).toHaveTextContent(
      'KCSE · 2025/2026 · Effective 1 March 2025 · Verification: Historical',
    )
    expect(within(historicalReference).getByRole('link', { name: 'Open historical admission source' })).toHaveAttribute(
      'href', 'https://students.kuccps.net/',
    )
    expect(within(detail).getByText('Official criteria unavailable')).toBeInTheDocument()
    expect(detail).toHaveTextContent(
      'Official placement criteria are unavailable for this framework and catalogue reference. Smarta Shauri does not substitute a formula or threshold.',
    )
    expect(detail).not.toHaveTextContent(/eligible|ineligible|probability|CBC admission score|admission prediction/i)
  })

  it('saves institution-only primary and programme-specific alternative goals', async () => {
    const user = userEvent.setup()
    renderPage()
    await selectInstitution(user)

    await user.selectOptions(screen.getByLabelText('Goal scope'), 'institution')
    await user.selectOptions(screen.getByLabelText('Goal slot'), 'primary')
    await user.click(screen.getByRole('button', { name: 'Save education goal' }))
    expect(await screen.findByText('Education goal saved.')).toBeInTheDocument()
    expect(await screen.findByText('Institution-wide exploration')).toBeInTheDocument()

    await user.click(await screen.findByRole('button', { name: 'View BSc Computer Science' }))
    await user.selectOptions(screen.getByLabelText('Goal scope'), 'programme')
    await user.selectOptions(screen.getByLabelText('Goal slot'), 'alternative-2')
    await user.click(screen.getByRole('button', { name: 'Save education goal' }))
    expect(await screen.findByRole('article', { name: 'Alternative 2 education goal' })).toBeInTheDocument()
  })

  it('communicates one primary and two-alternative limits and surfaces a backend limit failure', async () => {
    server.use(http.post('/api/v1/students/education-goals/', () => HttpResponse.json({
      data: null,
      error: true,
      message: 'You can save one primary goal and up to two alternatives.',
    }, { status: 400 })))
    const user = userEvent.setup()
    renderPage()
    await selectInstitution(user)

    expect(screen.getByText('1 primary + up to 2 alternatives')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Alternative 1 (already used)' })).toBeDisabled()
    await user.selectOptions(screen.getByLabelText('Goal slot'), 'primary')
    await user.click(screen.getByRole('button', { name: 'Save education goal' }))

    expect(await screen.findByText('You can save one primary goal and up to two alternatives.')).toBeInTheDocument()
  })

  it('searches and filters catalogue requests and explains empty results', async () => {
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('button', { name: 'Explore University of Nairobi' })
    await user.type(screen.getByLabelText('Search institutions'), 'missing')
    expect(await screen.findByText('No institutions match these filters')).toBeInTheDocument()
    await user.clear(screen.getByLabelText('Search institutions'))
    await user.selectOptions(screen.getByLabelText('County'), 'Mombasa')
    expect(await screen.findByText('No institutions match these filters')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('County'), '')
    await selectInstitution(user)
    await user.type(screen.getByLabelText('Search programmes'), 'missing')
    expect(await screen.findByText('No programmes match this search')).toBeInTheDocument()
  })

  it('keeps independent loading and empty feedback for goals and institutions', async () => {
    server.use(
      http.get('/api/v1/students/education-goals/', async () => {
        await delay('infinite')
        return HttpResponse.json({ data: [], error: null, message: '' })
      }),
      http.get('/api/v1/tertiary/institutions/', async () => {
        await delay('infinite')
        return HttpResponse.json({ data: [], error: null, message: '' })
      }),
    )
    const { unmount } = renderPage()

    expect(await screen.findByRole('status', { name: 'Loading saved education goals' })).toBeInTheDocument()
    expect(screen.getByRole('status', { name: 'Loading institutions' })).toBeInTheDocument()
    unmount()

    server.resetHandlers()
    server.use(
      http.get('/api/v1/students/education-goals/', () => HttpResponse.json({
        data: [], error: null, message: '',
      })),
      http.get('/api/v1/tertiary/institutions/', () => HttpResponse.json({
        data: [], error: null, message: '',
      })),
    )
    renderPage()
    expect(await screen.findByText('No education goals saved yet')).toBeInTheDocument()
    expect(await screen.findByText('No institutions match these filters')).toBeInTheDocument()
  })

  it('shows programme and selected-detail loading feedback in place', async () => {
    server.use(http.get('/api/v1/tertiary/programmes/', async () => {
      await delay('infinite')
      return HttpResponse.json({ data: [], error: null, message: '' })
    }))
    const user = userEvent.setup()
    const { unmount } = renderPage()
    await selectInstitution(user)

    expect(await screen.findByRole('status', { name: 'Loading programmes' })).toBeInTheDocument()
    unmount()

    server.resetHandlers()
    server.use(http.get('/api/v1/tertiary/programmes/:programmeId/', async () => {
      await delay('infinite')
      return HttpResponse.json({ data: programmeFixture, error: null, message: '' })
    }))
    renderPage()
    await selectProgramme(user)
    expect(await screen.findByRole('status', { name: 'Loading programme details' })).toBeInTheDocument()
  })

  it('retries failed goal and institution requests', async () => {
    let goalAttempts = 0
    let institutionAttempts = 0
    server.use(
      http.get('/api/v1/students/education-goals/', () => {
        goalAttempts += 1
        return goalAttempts === 1
          ? HttpResponse.json({ data: null, error: true, message: 'Failed.' }, { status: 500 })
          : HttpResponse.json({ data: [], error: null, message: '' })
      }),
      http.get('/api/v1/tertiary/institutions/', () => {
        institutionAttempts += 1
        return institutionAttempts === 1
          ? HttpResponse.json({ data: null, error: true, message: 'Failed.' }, { status: 500 })
          : HttpResponse.json({ data: [institutionFixture], error: null, message: '' })
      }),
    )
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: 'Retry saved goals' }))
    expect(await screen.findByText('No education goals saved yet')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Retry institutions' }))
    expect(await screen.findByRole('button', { name: 'Explore University of Nairobi' })).toBeInTheDocument()
    expect(goalAttempts).toBe(2)
    expect(institutionAttempts).toBe(2)
  })

  it('retries programme and selected-detail failures without losing the chosen institution', async () => {
    let programmeAttempts = 0
    let detailAttempts = 0
    server.use(
      http.get('/api/v1/tertiary/programmes/', () => {
        programmeAttempts += 1
        return programmeAttempts === 1
          ? HttpResponse.json({ data: null, error: true, message: 'Failed.' }, { status: 500 })
          : HttpResponse.json({ data: [programmeFixture], error: null, message: '' })
      }),
      http.get('/api/v1/tertiary/programmes/:programmeId/', () => {
        detailAttempts += 1
        return detailAttempts === 1
          ? HttpResponse.json({ data: null, error: true, message: 'Failed.' }, { status: 500 })
          : HttpResponse.json({ data: programmeFixture, error: null, message: '' })
      }),
    )
    const user = userEvent.setup()
    renderPage()
    await selectInstitution(user)
    await user.click(await screen.findByRole('button', { name: 'Retry programmes' }))
    await user.click(await screen.findByRole('button', { name: 'View BSc Computer Science' }))
    await user.click(await screen.findByRole('button', { name: 'Retry programme details' }))

    expect(await screen.findByRole('region', { name: 'BSc Computer Science details' })).toBeInTheDocument()
    expect(programmeAttempts).toBe(2)
    expect(detailAttempts).toBe(2)
  })

  it('updates and deletes existing goals with success toasts', async () => {
    const user = userEvent.setup()
    renderPage()

    const goal = await screen.findByRole('article', { name: 'Alternative 1 education goal' })
    await user.selectOptions(within(goal).getByLabelText('Change goal slot'), 'alternative-2')
    await user.click(within(goal).getByRole('button', { name: 'Update goal' }))
    expect(await screen.findByText('Education goal updated.')).toBeInTheDocument()
    await user.click(within(goal).getByRole('button', { name: 'Remove goal' }))
    expect(await screen.findByText('Education goal removed.')).toBeInTheDocument()
  })

  it('uses standard failure toasts for update and delete actions', async () => {
    server.use(
      http.patch('/api/v1/students/education-goals/:goalId/', () => HttpResponse.json(
        { data: null, error: true, message: 'Raw server response.' }, { status: 500 },
      )),
      http.delete('/api/v1/students/education-goals/:goalId/', () => HttpResponse.json(
        { data: null, error: true, message: 'Raw forbidden response.' }, { status: 403 },
      )),
    )
    const user = userEvent.setup()
    renderPage()
    const goal = await screen.findByRole('article', { name: 'Alternative 1 education goal' })

    await user.click(within(goal).getByRole('button', { name: 'Update goal' }))
    expect(await screen.findByText('Server error. Please try again in a moment.')).toBeInTheDocument()
    await user.click(within(goal).getByRole('button', { name: 'Remove goal' }))
    expect(await screen.findByText("You don't have permission to do that.")).toBeInTheDocument()
  })

  it('provides labelled keyboard-operable controls and a My Progress cross-link', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(screen.getByRole('link', { name: 'Back to My Progress' })).toHaveAttribute('href', '/grades')
    const institutionSearch = screen.getByLabelText('Search institutions')
    institutionSearch.focus()
    expect(institutionSearch).toHaveFocus()
    await user.keyboard('Nairobi')
    await selectInstitution(user)
    const institutionSource = screen.getByRole('region', { name: 'Selected institution source' })
    expect(institutionSource).toHaveTextContent(
      'KCSE · 2025/2026 · Effective 1 March 2025 · Verification: Historical',
    )
    expect(within(institutionSource).getByRole('link', { name: 'Open institution source' })).toHaveAttribute(
      'href', 'https://students.kuccps.net/',
    )
    expect(screen.getByLabelText('Search programmes')).toBeInTheDocument()
    expect(screen.getByLabelText('Goal scope')).toBeInTheDocument()
    expect(screen.getByLabelText('Goal slot')).toBeInTheDocument()
  })
})
