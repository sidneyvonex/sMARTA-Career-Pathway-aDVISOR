import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import LearnerPlanPage from '../pages/LearnerPlanPage'
import { server } from './msw/server'

const combination = {
  id: 1,
  code: 'ST1042',
  title: 'Agriculture, Biology & Chemistry',
  description: 'Curated pilot science option.',
  related_routes: ['Agricultural science'],
  framework: {
    code: 'CBC-SS-PILOT-2026',
    title: 'CBC Senior School Pilot Catalogue 2026',
    source_url: 'https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf',
    effective_date: '2026-01-01',
  },
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
}

const choice = {
  id: 4,
  combination,
  status: 'provisional',
  learner_reason: '',
  created_at: '2026-07-30T10:00:00Z',
  updated_at: '2026-07-30T10:00:00Z',
}

const plan = {
  id: 7,
  provisional_choice: choice,
  learner_reason: 'I enjoy science and practical projects.',
  review_status: 'draft',
  reviewed_at: null,
  milestones: [
    {
      id: 9,
      title: 'Review pilot school offerings',
      due_date: '2026-09-15',
      is_complete: false,
      completed_at: null,
      position: 0,
      created_at: '2026-07-30T10:00:00Z',
      updated_at: '2026-07-30T10:00:00Z',
    },
  ],
  created_at: '2026-07-30T10:00:00Z',
  updated_at: '2026-07-30T10:00:00Z',
}

function renderPlan() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <LearnerPlanPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LearnerPlanPage', () => {
  it('directs a learner without a provisional choice to comparison', async () => {
    renderPlan()

    expect(await screen.findByRole('heading', { name: 'Your plan needs a combination' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Compare saved choices' })).toHaveAttribute('href', '/compare')
  })

  it('shows evidence, milestones, status and saves checklist progress', async () => {
    let milestoneCompleted = false
    server.use(
      http.get('/api/v1/students/combination-choices/', () => HttpResponse.json({
        data: [choice],
        error: null,
        message: '',
      })),
      http.get('/api/v1/students/plan/', () => HttpResponse.json({
        data: {
          ...plan,
          milestones: plan.milestones.map((item) => ({
            ...item,
            is_complete: milestoneCompleted,
            completed_at: milestoneCompleted ? '2026-07-30T12:00:00Z' : null,
          })),
        },
        error: null,
        message: '',
      })),
      http.put('/api/v1/students/plan/milestones/:id/', async ({ request }) => {
        const body = await request.json() as { is_complete: boolean }
        milestoneCompleted = body.is_complete
        return HttpResponse.json({
          data: {
            ...plan.milestones[0],
            is_complete: milestoneCompleted,
            completed_at: milestoneCompleted ? '2026-07-30T12:00:00Z' : null,
          },
          error: null,
          message: 'Milestone updated.',
        })
      }),
    )
    renderPlan()

    expect(await screen.findByRole('heading', { name: 'Build evidence around your choice' })).toBeInTheDocument()
    expect(screen.getByText('Agriculture, Biology & Chemistry')).toBeInTheDocument()
    expect(screen.getByText('Draft')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Core evidence ready' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('checkbox', { name: /Review pilot school offerings/i }))

    await waitFor(() => expect(milestoneCompleted).toBe(true))
    await waitFor(() => expect(screen.getByText('1 of 1 complete')).toBeInTheDocument())
  })

  it('starts a plan from the selected provisional choice', async () => {
    let submittedReason = ''
    server.use(
      http.get('/api/v1/students/combination-choices/', () => HttpResponse.json({
        data: [choice],
        error: null,
        message: '',
      })),
      http.put('/api/v1/students/plan/', async ({ request }) => {
        const body = await request.json() as { learner_reason: string }
        submittedReason = body.learner_reason
        return HttpResponse.json({
          data: { ...plan, learner_reason: submittedReason, milestones: [] },
          error: null,
          message: 'Learner plan created.',
        }, { status: 201 })
      }),
    )
    renderPlan()

    const reason = await screen.findByLabelText('Why are you considering this combination?')
    fireEvent.change(reason, { target: { value: 'I want to explore agricultural science.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Start my plan' }))

    await waitFor(() => expect(submittedReason).toBe('I want to explore agricultural science.'))
  })
})
