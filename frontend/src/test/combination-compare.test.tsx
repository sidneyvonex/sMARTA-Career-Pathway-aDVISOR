import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import CombinationComparePage from '../pages/CombinationComparePage'
import { server } from './msw/server'


const framework = {
  code: 'CBC-SS-PILOT-2026',
  title: 'CBC Senior School Pilot Catalogue 2026',
  source_url: 'https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf',
  effective_date: '2026-01-01',
}

const combinations = [
  {
    id: 1,
    code: 'ST1042',
    title: 'Agriculture, Biology & Chemistry',
    description: 'Curated pilot science option.',
    related_routes: ['Agricultural science', 'Biological science'],
    framework,
    track: {
      id: 1,
      code: 'PURE-SCIENCES',
      name: 'Pure Sciences',
      description: 'Pilot track',
      is_active: true,
      pathway: { id: 1, name: 'STEM', description: 'STEM pathway' },
    },
    subjects: [
      { id: 1, code: 'AGR10', name: 'Agriculture', grade: 10, category: 'Elective' },
      { id: 2, code: 'BIO10', name: 'Biology', grade: 10, category: 'Elective' },
      { id: 3, code: 'CHE10', name: 'Chemistry', grade: 10, category: 'Elective' },
    ],
    offered_schools: [
      { id: 1, school_code: 'PILOT-KIA-001', name: 'Kiambu Pilot School', county: 'kiambu' },
    ],
  },
  {
    id: 2,
    code: 'SS2019',
    title: 'Religious Education, Geography & History',
    description: 'Curated pilot humanities option.',
    related_routes: ['Education', 'Public service'],
    framework,
    track: {
      id: 2,
      code: 'HUMANITIES-BUSINESS',
      name: 'Humanities & Business Studies',
      description: 'Pilot track',
      is_active: true,
      pathway: { id: 2, name: 'Social Sciences', description: 'Social Sciences pathway' },
    },
    subjects: [
      { id: 4, code: 'CHR10', name: 'Religious Education', grade: 10, category: 'Elective' },
      { id: 5, code: 'GEO10', name: 'Geography', grade: 10, category: 'Elective' },
      { id: 6, code: 'HCT10', name: 'History', grade: 10, category: 'Elective' },
    ],
    offered_schools: [],
  },
]

function renderCompare() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CombinationComparePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('CombinationComparePage', () => {
  it('asks for two choices when the comparison set is too small', async () => {
    renderCompare()
    expect(await screen.findByRole('heading', { name: 'Save at least two combinations' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Explore combinations' })).toHaveAttribute('href', '/explore')
  })

  it('compares two saved combinations as stacked evidence sections', async () => {
    server.use(
      http.get('/api/v1/students/combination-choices/', () => HttpResponse.json({
        data: combinations.map((combination, index) => ({
          id: index + 1,
          status: 'saved',
          learner_reason: '',
          created_at: '2026-07-30T10:00:00Z',
          updated_at: '2026-07-30T10:00:00Z',
          combination,
        })),
        error: null,
        message: '',
      })),
    )
    renderCompare()

    expect(await screen.findByRole('heading', { name: 'Compare your saved combinations' })).toBeInTheDocument()
    for (const heading of [
      'Pathway and track',
      'Three elective subjects',
      'Interest evidence',
      'Academic evidence',
      'Verified school offerings',
      'Related routes and careers',
      'Evidence gaps',
    ]) {
      expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument()
    }
    expect(screen.getByText('Agricultural science')).toBeInTheDocument()
    expect(screen.getByText('Public service')).toBeInTheDocument()
    expect(screen.getByText('Kiambu Pilot School')).toBeInTheDocument()
    expect(screen.getAllByText('Not recorded').length).toBeGreaterThan(0)
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
