import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ProgressAssessment, ProgressEvidence, SubjectProgress } from '../api/students'
import { getBaseNavItems } from '../components/shell/navItems'
import GradeEntryForm from '../components/students/GradeEntryForm'
import GradesPage from '../pages/GradesPage'
import { academicGoalFixture } from './msw/handlers'
import { server } from './msw/server'


const makeEvidence = (
  id: number,
  level: ProgressEvidence['level'],
  rank: number,
  academicGrade: ProgressEvidence['academic_grade'],
  year: number,
  term: ProgressEvidence['term'],
  source: ProgressEvidence['source'] = 'learner',
): ProgressEvidence => ({
  id,
  academic_grade: academicGrade,
  year,
  term,
  level,
  rank,
  framework: { code: 'CBC-SENIOR-SCHOOL', version: 'pilot-2026' },
  source,
  verified_by: source === 'school' ? 9 : null,
  verified_school: source === 'school' ? 3 : null,
  verified_at: source === 'school' ? '2026-07-30T10:00:00Z' : null,
  created_at: '2026-07-30T10:00:00Z',
})

const subject = (
  continuityCode: string,
  subjectName: string,
  status: SubjectProgress['status'],
  label: string,
  ruleCode: SubjectProgress['rule_code'],
  evidence: ProgressEvidence[],
  confidence: SubjectProgress['evidence_confidence'] = 'learner_entered',
): SubjectProgress => ({
  continuity_code: continuityCode,
  subject_name: subjectName,
  status,
  label,
  rule_code: ruleCode,
  explanation: `${subjectName} status is based on the displayed academic evidence.`,
  suggested_action: `Review the next ${subjectName} learning activity.`,
  evidence_confidence: confidence,
  records_used: evidence.slice(-2),
  evidence,
  decision_inputs: {
    latest_framework: evidence[evidence.length - 1]?.framework ?? null,
    me2_rank: 5,
  },
})

const mathematicsEvidence = [
  makeEvidence(1, 'AE2', 3, 10, 2025, 3),
  {
    ...makeEvidence(2, 'ME2', 5, 10, 2026, 1),
    verified_by: 9,
    verified_school: 3,
    verified_at: '2026-07-30T10:00:00Z',
  },
]

const progressFixture: ProgressAssessment = {
  subjects: [
    subject(
      'MTH', 'Mathematics', 'strong', 'Strong',
      'latest_ee_or_improving_to_me2_strong', mathematicsEvidence, 'mixed',
    ),
    subject(
      'ENG', 'English', 'on_track', 'On track', 'otherwise_me_on_track',
      [makeEvidence(3, 'ME2', 5, 9, 2025, 2)],
    ),
    subject(
      'BIO', 'Biology', 'needs_attention', 'Needs attention',
      'latest_ae_or_two_declines_attention',
      [makeEvidence(4, 'ME2', 5, 10, 2026, 1), makeEvidence(5, 'AE1', 4, 10, 2026, 2)],
    ),
    subject(
      'CHE', 'Chemistry', 'support', 'Support', 'latest_be_support',
      [makeEvidence(6, 'BE1', 2, 10, 2026, 2)],
    ),
    subject(
      'PHY', 'Physics', 'insufficient_evidence', 'Insufficient evidence',
      'missing_evidence', [],
    ),
  ],
  overall: {
    status: 'support',
    label: 'Support',
    subject_continuity_codes: ['CHE'],
  },
  advisory_disclaimer: 'Academic progress is advisory only. It does not determine official CBE placement or admission.',
}

function progressResponse(data: ProgressAssessment = progressFixture) {
  return HttpResponse.json({ data, error: null, message: '' })
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <GradesPage />
        <Toaster />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function renderGradeForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <GradeEntryForm studentSubjectId={10} />
      <Toaster />
    </QueryClientProvider>,
  )
}

describe('flagged My Progress dashboard', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'true')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('summarises every readiness status with explainable evidence and an accessible trend table', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse()))

    renderPage()

    expect(await screen.findByRole('heading', { name: 'My progress', level: 1 })).toBeInTheDocument()
    expect(screen.getByText('5 subjects reviewed')).toBeInTheDocument()
    for (const label of ['Strong', 'On track', 'Needs attention', 'Support', 'Insufficient evidence']) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0)
    }
    expect(screen.getByText(
      'Improving from Approaching Expectation - Level 2 to Meeting Expectation - Level 2 across 2 status records.',
    )).toBeInTheDocument()
    expect(screen.getByText('Mixed learner-entered and school-verified evidence')).toBeInTheDocument()
    expect(screen.getAllByText('CBC-SENIOR-SCHOOL pilot-2026').length).toBeGreaterThan(0)
    expect(screen.getByText('Rule: latest_ee_or_improving_to_me2_strong')).toBeInTheDocument()
    expect(screen.getByText('Review the next Mathematics learning activity.')).toBeInTheDocument()

    const evidenceTable = screen.getByRole('table', { name: 'Mathematics evidence' })
    expect(within(evidenceTable).getByText('Grade 10, 2026, Term 1')).toBeInTheDocument()
    expect(within(evidenceTable).getByText(/School verified on/)).toBeInTheDocument()
    const recordsUsed = screen.getByRole('table', {
      name: 'Mathematics evidence used for this status',
    })
    expect(within(recordsUsed).getByText('Grade 10, 2025, Term 3')).toBeInTheDocument()
    expect(within(recordsUsed).getAllByText('CBC-SENIOR-SCHOOL pilot-2026')).toHaveLength(2)
    expect(within(recordsUsed).getAllByText('Learner entered')).toHaveLength(2)
    expect(within(recordsUsed).getByText(/School verified/)).toBeInTheDocument()
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
    expect(screen.getByText(progressFixture.advisory_disclaimer)).toBeInTheDocument()
  })

  it('uses a singular subject label when one subject is reviewed', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse({
      ...progressFixture,
      subjects: progressFixture.subjects.slice(0, 1),
      overall: { status: 'strong', label: 'Strong', subject_continuity_codes: ['MTH'] },
    })))

    renderPage()

    expect(await screen.findByText('1 subject reviewed')).toBeInTheDocument()
    expect(screen.queryByText('1 subjects reviewed')).not.toBeInTheDocument()
  })

  it('filters the evidence view by academic grade and year with associated labels', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse()))
    const user = userEvent.setup()

    renderPage()
    await screen.findByRole('heading', { name: 'My progress' })

    const gradeFilter = screen.getByLabelText('Academic grade')
    const yearFilter = screen.getByLabelText('Academic year')
    await user.selectOptions(gradeFilter, '9')
    expect(screen.getByRole('heading', { name: 'English' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Mathematics' })).not.toBeInTheDocument()

    await user.selectOptions(gradeFilter, 'all')
    await user.selectOptions(yearFilter, '2026')
    expect(screen.getByRole('heading', { name: 'Mathematics' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'English' })).not.toBeInTheDocument()
  })

  it('keeps trend copy tied to the unfiltered winning-rule evidence', async () => {
    const chronology = [
      makeEvidence(31, 'BE1', 2, 9, 2025, 3),
      makeEvidence(32, 'EE1', 8, 10, 2026, 1),
      makeEvidence(33, 'ME1', 6, 10, 2026, 2),
    ]
    const declining = subject(
      'MTH',
      'Mathematics',
      'needs_attention',
      'Needs attention',
      'latest_ae_or_two_declines_attention',
      chronology,
    )
    declining.records_used = chronology.slice(-2)
    server.use(http.get('/api/v1/students/progress/', () => progressResponse({
      ...progressFixture,
      subjects: [declining],
      overall: {
        status: 'needs_attention',
        label: 'Needs attention',
        subject_continuity_codes: ['MTH'],
      },
    })))
    const user = userEvent.setup()

    renderPage()
    expect(await screen.findByText(
      'Declining from Exceeding Expectation - Level 1 to Meeting Expectation - Level 1 across 2 status records.',
    )).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Academic grade'), '9')
    expect(screen.getByText(
      'Declining from Exceeding Expectation - Level 1 to Meeting Expectation - Level 1 across 2 status records.',
    )).toBeInTheDocument()
    expect(screen.getByRole('table', {
      name: 'Mathematics evidence used for this status',
    })).toBeInTheDocument()
  })

  it('creates an academic target from a fully labelled keyboard-operable form and shows its toast', async () => {
    server.use(
      http.get('/api/v1/students/progress/', () => progressResponse()),
      http.get('/api/v1/students/academic-goals/', () => HttpResponse.json({
        data: [], error: null, message: '',
      })),
    )
    const user = userEvent.setup()

    renderPage()
    await screen.findByRole('heading', { name: 'My progress' })
    const setTarget = screen.getByRole('button', { name: 'Set an academic target' })
    setTarget.focus()
    expect(setTarget).toHaveFocus()
    await user.keyboard('{Enter}')

    await user.selectOptions(screen.getByLabelText('Subject'), 'MTH')
    await user.selectOptions(screen.getByLabelText('Target level'), 'ME1')
    await user.selectOptions(screen.getByLabelText('Target term'), '3')
    await user.clear(screen.getByLabelText('Target year'))
    await user.type(screen.getByLabelText('Target year'), '2027')
    await user.selectOptions(screen.getByLabelText('Target academic grade'), '10')
    await user.type(screen.getByLabelText('Action plan'), 'Practise twice each week.')
    await user.click(screen.getByRole('button', { name: 'Create target' }))

    expect(await screen.findByText('Academic goal created.')).toBeInTheDocument()
  })

  it('supports academic-target readiness, update, confirmation, close, and lifecycle history', async () => {
    const activeReady = academicGoalFixture({ id: 12, continuity_code: 'MTH' })
    const activeWaiting = academicGoalFixture({
      id: 13,
      continuity_code: 'ENG',
      ready_for_achievement: false,
      readiness_evidence: null,
    })
    let goals = [
      activeReady,
      activeWaiting,
      academicGoalFixture({
        id: 14,
        continuity_code: 'BIO',
        status: 'achieved',
        achieved_at: '2026-08-01T10:00:00Z',
      }),
      academicGoalFixture({
        id: 15,
        continuity_code: 'CHE',
        status: 'closed',
        closed_at: '2026-08-01T10:00:00Z',
      }),
    ]
    server.use(
      http.get('/api/v1/students/progress/', () => progressResponse()),
      http.get('/api/v1/students/academic-goals/', () => HttpResponse.json({
        data: goals, error: null, message: '',
      })),
      http.patch('/api/v1/students/academic-goals/12/', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>
        await delay(80)
        goals = goals.map((goal) => goal.id === 12
          ? { ...goal, action_plan: body.action_plan as string }
          : goal)
        return HttpResponse.json({
          data: goals.find((goal) => goal.id === 12),
          error: null,
          message: 'Academic goal updated.',
        })
      }),
      http.post('/api/v1/students/academic-goals/12/confirm-achievement/', () => {
        goals = goals.map((goal) => goal.id === 12
          ? { ...goal, status: 'achieved' as const, achieved_at: '2026-08-02T10:00:00Z' }
          : goal)
        return HttpResponse.json({
          data: goals.find((goal) => goal.id === 12),
          error: null,
          message: 'Academic goal achieved.',
        })
      }),
      http.delete('/api/v1/students/academic-goals/13/', () => {
        goals = goals.map((goal) => goal.id === 13
          ? { ...goal, status: 'closed' as const, closed_at: '2026-08-02T10:00:00Z' }
          : goal)
        return HttpResponse.json({
          data: goals.find((goal) => goal.id === 13),
          error: null,
          message: 'Academic goal closed.',
        })
      }),
    )
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const user = userEvent.setup()

    renderPage()
    expect(await screen.findByText('Ready to confirm achievement')).toBeInTheDocument()
    expect(screen.getByText('Waiting for later evidence')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Target history' })).toBeInTheDocument()
    expect(screen.getByText('Achieved')).toBeInTheDocument()
    expect(screen.getByText('Closed')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Edit Mathematics target' }))
    await user.clear(screen.getByLabelText('Action plan'))
    await user.type(screen.getByLabelText('Action plan'), 'Attend weekly support sessions.')
    await user.click(screen.getByRole('button', { name: 'Update target' }))
    expect(screen.getByRole('button', { name: 'Updating target…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()
    expect(await screen.findByText('Academic goal updated.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Confirm Mathematics achieved' }))
    expect(confirm).toHaveBeenCalledWith(
      'Confirm that Mathematics has achieved this target using the latest qualifying evidence?',
    )
    expect(await screen.findByText('Academic goal achieved.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Close English target' }))
    expect(confirm).toHaveBeenCalledWith(
      'Close the English target? It will remain in target history.',
    )
    expect(await screen.findByText('Academic goal closed.')).toBeInTheDocument()
    await waitFor(() => expect(screen.getAllByText('Achieved')).toHaveLength(2))
    expect(screen.getAllByText('Closed')).toHaveLength(2)
  })

  it('previews education goals without presenting admission claims', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse()))

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Education goal preview' })).toBeInTheDocument()
    expect(screen.getByText('University of Nairobi')).toBeInTheDocument()
    expect(screen.getByText('BSc Computer Science')).toBeInTheDocument()
    expect(screen.getByText(/KCSE · 2025\/2026 .* Historical reference only/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open programme source' })).toHaveAttribute(
      'href', 'https://students.kuccps.net/',
    )
    expect(screen.getByRole('link', { name: 'Explore education goals' })).toHaveAttribute(
      'href', '/education-goals',
    )
    expect(screen.queryByText(/eligible|probability|admission chance/i)).not.toBeInTheDocument()
  })

  it('shows a page-shaped loading state while progress is loading', async () => {
    server.use(http.get('/api/v1/students/progress/', async () => {
      await delay('infinite')
      return progressResponse()
    }))

    renderPage()

    expect(await screen.findByRole('status', { name: 'Loading academic progress' })).toBeInTheDocument()
  })

  it('keeps result recording disabled while enrolled subjects are loading', async () => {
    server.use(
      http.get('/api/v1/students/progress/', () => progressResponse()),
      http.get('/api/v1/students/my-subjects/', async () => {
        await delay('infinite')
        return HttpResponse.json({ data: [], error: null, message: '' })
      }),
    )

    renderPage()

    const recordResult = await screen.findByRole('button', { name: 'Record a result' })
    expect(recordResult).toBeDisabled()
    expect(screen.getByRole('status', { name: 'Loading enrolled subjects' })).toBeInTheDocument()
  })

  it('shows an academic-target loading state without false empty or creation UI', async () => {
    server.use(
      http.get('/api/v1/students/progress/', () => progressResponse()),
      http.get('/api/v1/students/academic-goals/', async () => {
        await delay('infinite')
        return HttpResponse.json({ data: [], error: null, message: '' })
      }),
    )

    renderPage()

    expect(await screen.findByRole('status', { name: 'Loading academic targets' })).toBeInTheDocument()
    expect(screen.queryByText('You have no active academic targets yet.')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Set an academic target' })).not.toBeInTheDocument()
  })

  it('shows an education-goal loading state without a false empty message', async () => {
    server.use(
      http.get('/api/v1/students/progress/', () => progressResponse()),
      http.get('/api/v1/students/education-goals/', async () => {
        await delay('infinite')
        return HttpResponse.json({ data: [], error: null, message: '' })
      }),
    )

    renderPage()

    expect(await screen.findByRole('status', { name: 'Loading education goals' })).toBeInTheDocument()
    expect(screen.queryByText('No education goal has been saved yet.')).not.toBeInTheDocument()
  })

  it('refreshes the progress summary after saving new grade evidence', async () => {
    let progressRequests = 0
    let goalRequests = 0
    server.use(http.get('/api/v1/students/progress/', () => {
      progressRequests += 1
      return progressResponse(progressRequests === 1 ? progressFixture : {
        ...progressFixture,
        overall: { status: 'strong', label: 'Strong', subject_continuity_codes: ['MTH'] },
      })
    }), http.get('/api/v1/students/academic-goals/', () => {
      goalRequests += 1
      return HttpResponse.json({ data: [], error: null, message: '' })
    }))
    const user = userEvent.setup()

    renderPage()
    const summary = await screen.findByLabelText('Academic progress summary')
    expect(within(summary).getByText('Support')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Record a result' }))
    await user.click(screen.getByRole('button', { name: 'Add grade' }))

    expect(await within(summary).findByText('Strong')).toBeInTheDocument()
    expect(progressRequests).toBe(2)
    await waitFor(() => expect(goalRequests).toBe(2))
  })

  it('preserves subject enrolment and archive management on the unified page', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const user = userEvent.setup()

    renderPage()
    expect(await screen.findByRole('heading', { name: 'Manage subjects' })).toBeInTheDocument()

    await user.click(await screen.findByRole('button', { name: 'Add English' }))
    expect(await screen.findByText('English added to your subjects.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Archive Mathematics' }))
    expect(confirm).toHaveBeenCalledWith(
      'Archive Mathematics? Its existing grade history will be preserved.',
    )
    expect(await screen.findByText('Mathematics removed.')).toBeInTheDocument()
  })

  it('offers subject enrolment instead of a dead-end record action when none are active', async () => {
    server.use(
      http.get('/api/v1/students/my-subjects/', () => HttpResponse.json({
        data: [], error: null, message: '',
      })),
      http.get('/api/v1/students/progress/', () => progressResponse({
        ...progressFixture,
        subjects: [],
        overall: {
          status: 'insufficient_evidence',
          label: 'Insufficient evidence',
          subject_continuity_codes: [],
        },
      })),
    )

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Manage subjects' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Add Mathematics' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Record your first result' })).not.toBeInTheDocument()
  })

  it('edits and deletes only mutable evidence and refreshes goal readiness', async () => {
    let goalRequests = 0
    let updateRequests = 0
    let deleteRequests = 0
    server.use(
      http.get('/api/v1/students/academic-goals/', () => {
        goalRequests += 1
        return HttpResponse.json({ data: [], error: null, message: '' })
      }),
      http.get('/api/v1/students/my-subjects/:id/grades/', () => HttpResponse.json({
        data: [
          {
            id: 20, term: 1, year: 2026, level: 'ME1', source: 'learner',
            verified_by: null, verified_school: null, verified_at: null,
            created_at: '2026-06-14T10:00:00Z', updated_at: '2026-06-14T10:00:00Z',
          },
          {
            id: 21, term: 2, year: 2026, level: 'EE2', source: 'learner',
            verified_by: null, verified_school: 3, verified_at: null,
            created_at: '2026-07-14T10:00:00Z', updated_at: '2026-07-14T10:00:00Z',
          },
        ],
        error: null,
        message: '',
      })),
      http.put('/api/v1/students/my-subjects/:subjectId/grades/:gradeId/', async ({ request }) => {
        updateRequests += 1
        const body = await request.json() as Record<string, unknown>
        return HttpResponse.json({
          data: {
            id: 20, term: body.term, year: body.year, level: body.level,
            source: 'learner', verified_by: null, verified_school: null, verified_at: null,
            created_at: '2026-06-14T10:00:00Z', updated_at: '2026-08-02T10:00:00Z',
          },
          error: null,
          message: 'Grade updated.',
        })
      }),
      http.delete('/api/v1/students/my-subjects/:subjectId/grades/:gradeId/', () => {
        deleteRequests += 1
        return HttpResponse.json({ data: null, error: null, message: 'Grade deleted.' })
      }),
    )
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const user = userEvent.setup()

    renderPage()
    await user.click(await screen.findByRole('button', { name: 'Record a result' }))
    expect(await screen.findByRole('button', { name: 'Edit Term 1 2026' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete Term 1 2026' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit Term 2 2026' })).not.toBeInTheDocument()
    expect(screen.getByText('Verification removed; school provenance retained')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Edit Term 1 2026' }))
    await user.selectOptions(screen.getByLabelText('Edit level for Term 1 2026'), 'EE1')
    await user.click(screen.getByRole('button', { name: 'Save grade changes' }))
    expect(await screen.findByText('Grade updated.')).toBeInTheDocument()
    expect(updateRequests).toBe(1)

    await user.click(screen.getByRole('button', { name: 'Delete Term 1 2026' }))
    expect(await screen.findByText('Grade entry removed.')).toBeInTheDocument()
    expect(deleteRequests).toBe(1)
    await waitFor(() => expect(goalRequests).toBeGreaterThanOrEqual(3))
  })

  it('uses the term-specific grade-saved toast after a successful save', async () => {
    const user = userEvent.setup()
    renderGradeForm()

    await user.selectOptions(screen.getByLabelText('Term'), '2')
    await user.click(screen.getByRole('button', { name: 'Add grade' }))

    expect(await screen.findByText('Grade saved for Term 2.')).toBeInTheDocument()
  })

  it('uses the standard permission toast when grade saving is forbidden', async () => {
    server.use(http.post('/api/v1/students/my-subjects/:id/grades/', () => HttpResponse.json(
      { data: null, error: true, message: 'Raw forbidden response.' },
      { status: 403 },
    )))
    const user = userEvent.setup()
    renderGradeForm()

    await user.click(screen.getByRole('button', { name: 'Add grade' }))

    expect(await screen.findByText("You don't have permission to do that.")).toBeInTheDocument()
  })

  it('uses the standard connection toast when grade saving has no response', async () => {
    server.use(http.post('/api/v1/students/my-subjects/:id/grades/', () => HttpResponse.error()))
    const user = userEvent.setup()
    renderGradeForm()

    await user.click(screen.getByRole('button', { name: 'Add grade' }))

    expect(await screen.findByText('Connection error. Please check your internet.')).toBeInTheDocument()
  })

  it('recovers from a progress error through the retry action', async () => {
    let attempts = 0
    server.use(http.get('/api/v1/students/progress/', () => {
      attempts += 1
      return attempts === 1
        ? HttpResponse.json({ data: null, error: true, message: 'Failed.' }, { status: 500 })
        : progressResponse()
    }))
    const user = userEvent.setup()

    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Academic progress could not load')
    await user.click(screen.getByRole('button', { name: 'Retry progress' }))
    expect(await screen.findByText('5 subjects reviewed')).toBeInTheDocument()
    expect(attempts).toBe(2)
  })

  it('invites the learner to record evidence when no subject progress exists', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse({
      ...progressFixture,
      subjects: [],
      overall: { status: 'insufficient_evidence', label: 'Insufficient evidence', subject_continuity_codes: [] },
    })))

    renderPage()

    expect(await screen.findByText('Start your academic evidence')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Record your first result' })).toBeInTheDocument()
  })

  it('keeps the legacy grade experience and navigation label when the flag is off', async () => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'false')

    renderPage()

    expect(await screen.findByRole('heading', { name: 'My subjects & grades' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'My progress' })).not.toBeInTheDocument()
    expect(getBaseNavItems('student').find((item) => item.to === '/grades')?.label).toBe('My Grades')
  })

  it('uses the My Progress navigation label only while the flag is on', () => {
    expect(getBaseNavItems('student').find((item) => item.to === '/grades')).toMatchObject({
      label: 'My Progress',
      short: 'Progress',
    })
  })
})
