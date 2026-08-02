import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ProgressAssessment, ProgressEvidence, SubjectProgress } from '../api/students'
import { getBaseNavItems } from '../components/shell/navItems'
import GradeEntryForm from '../components/students/GradeEntryForm'
import GradesPage from '../pages/GradesPage'
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
  makeEvidence(2, 'ME2', 5, 10, 2026, 1, 'school'),
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
      'Improving from Approaching Expectation - Level 2 to Meeting Expectation - Level 2 across 2 records.',
    )).toBeInTheDocument()
    expect(screen.getByText('Mixed learner-entered and school-verified evidence')).toBeInTheDocument()
    expect(screen.getAllByText('CBC-SENIOR-SCHOOL pilot-2026').length).toBeGreaterThan(0)
    expect(screen.getByText('Rule: latest_ee_or_improving_to_me2_strong')).toBeInTheDocument()
    expect(screen.getByText('Review the next Mathematics learning activity.')).toBeInTheDocument()

    const evidenceTable = screen.getByRole('table', { name: 'Mathematics evidence' })
    expect(within(evidenceTable).getByText('Grade 10, 2026, Term 1')).toBeInTheDocument()
    expect(within(evidenceTable).getByText('School verified')).toBeInTheDocument()
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

  it('previews education goals without presenting admission claims', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse()))

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Education goal preview' })).toBeInTheDocument()
    expect(screen.getByText('University of Nairobi')).toBeInTheDocument()
    expect(screen.getByText('BSc Computer Science')).toBeInTheDocument()
    expect(screen.getByText(/historical catalogue reference/i)).toBeInTheDocument()
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
    server.use(http.get('/api/v1/students/progress/', () => {
      progressRequests += 1
      return progressResponse(progressRequests === 1 ? progressFixture : {
        ...progressFixture,
        overall: { status: 'strong', label: 'Strong', subject_continuity_codes: ['MTH'] },
      })
    }))
    const user = userEvent.setup()

    renderPage()
    const summary = await screen.findByLabelText('Academic progress summary')
    expect(within(summary).getByText('Support')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Record a result' }))
    await user.click(screen.getByRole('button', { name: 'Add grade' }))

    expect(await within(summary).findByText('Strong')).toBeInTheDocument()
    expect(progressRequests).toBe(2)
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
