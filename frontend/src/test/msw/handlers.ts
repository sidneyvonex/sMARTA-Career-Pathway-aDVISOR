import { http, HttpResponse } from 'msw'

const BASE = '/api/v1/auth'

export const handlers = [
  http.post(`${BASE}/login/`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string }
    if (body.password === 'wrong') {
      return HttpResponse.json({ data: null, error: true, message: 'Invalid email or password.' }, { status: 401 })
    }
    return HttpResponse.json({
      data: { user: { id: 1, email: body.email, first_name: 'Jane', last_name: 'Doe', role: 'student', county: 'kiambu', is_email_verified: true } },
      error: null,
      message: 'Login successful.',
    })
  }),

  http.post(`${BASE}/register/`, async ({ request }) => {
    const body = await request.json() as { email: string }
    if (body.email === 'existing@test.com') {
      return HttpResponse.json({ data: null, error: true, message: 'An account with this email already exists.' }, { status: 400 })
    }
    return HttpResponse.json({ data: null, error: null, message: 'Registration successful. Check your email.' }, { status: 201 })
  }),

  http.get(`${BASE}/me/`, () => {
    return HttpResponse.json({ data: null, error: true, message: 'Not authenticated.' }, { status: 401 })
  }),

  http.post(`${BASE}/logout/`, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Logged out.' })
  }),

  http.post(`${BASE}/token/refresh/`, () => {
    return HttpResponse.json({ data: null, error: true, message: 'No refresh token.' }, { status: 401 })
  }),

  // Students
  http.get('/api/v1/students/profile/', () => {
    return HttpResponse.json({
      data: {
        id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
        county: 'kiambu', grade: 9, mode: 'school_linked',
        school_membership_status: 'pending',
        bio: 'I love science', date_of_birth: null, career_interests: '',
        photo_url: null,
      },
      error: null, message: '',
    })
  }),

  http.patch('/api/v1/students/profile/', async ({ request }) => {
    const body = await request.json() as Record<string, string>
    return HttpResponse.json({
      data: {
        id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
        county: 'kiambu', grade: 9, mode: 'school_linked',
        school_membership_status: 'pending',
        bio: body.bio ?? 'I love science', date_of_birth: null,
        career_interests: body.career_interests ?? '', photo_url: null,
      },
      error: null, message: 'Profile updated.',
    })
  }),

  http.post('/api/v1/students/profile/photo/', () => {
    return HttpResponse.json({
      data: { photo_url: 'https://cdn.example.com/profile-photos/user_1.jpg' },
      error: null, message: 'Photo updated.',
    })
  }),

  http.delete('/api/v1/students/profile/photo/', () => {
    return HttpResponse.json({ data: null, error: null, message: 'Photo removed.' })
  }),

  http.get('/api/v1/students/subjects/', ({ request }) => {
    const url = new URL(request.url)
    const grade = Number(url.searchParams.get('grade') ?? '9')
    return HttpResponse.json({
      data: [
        grade === 10
          ? { id: 1, name: 'Core Mathematics', code: 'CMT10', grade, category: 'Elective', is_active: true }
          : { id: 1, name: 'Mathematics', code: 'MTH9', grade, category: 'Core', is_active: true },
        { id: 2, name: 'English', code: `ENG${grade}`, grade, category: 'Core', is_active: true },
      ],
      error: null, message: '',
    })
  }),

  http.get('/api/v1/students/my-subjects/', () => {
    return HttpResponse.json({
      data: [
        { id: 10, subject: { id: 1, name: 'Mathematics', code: 'MTH9', grade: 9, category: 'Core', is_active: true }, created_at: '2026-06-14T10:00:00Z' },
      ],
      error: null, message: '',
    })
  }),

  http.get('/api/v1/students/evidence-summary/', () => {
    return HttpResponse.json({
      data: {
        profile_completion: { status: 'complete', percent: 100, missing_fields: [] },
        academic_evidence: {
          status: 'ready',
          total_subjects: 3,
          subjects_with_evidence: 3,
          total_grade_records: 6,
        },
        assessment: {
          status: 'complete',
          instrument_version: 'riasec-pilot-1.0',
          submitted_at: '2026-07-30T10:00:00Z',
        },
        saved_combination_count: 2,
        plan_status: 'not_started',
        next_action: {
          code: 'compare_combinations',
          title: 'Compare your saved combinations',
          href: '/compare',
        },
      },
      error: null,
      message: '',
    })
  }),

  http.get('/api/v1/students/dashboard/', () => {
    return HttpResponse.json({
      data: {
        profile: {
          id: 1, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
          county: 'kiambu', grade: 9, mode: 'school_linked',
          school_membership_status: 'active',
          bio: 'I love science', date_of_birth: '2011-01-10',
          career_interests: 'Engineering', photo_url: null,
        },
        grade_summary: {
          status: 'ready',
          total_subjects: 3,
          subjects_with_evidence: 3,
          total_grade_records: 3,
          subjects: [
            {
              enrollment_id: 10,
              subject: {
                id: 1, name: 'Mathematics', code: 'MTH9',
                grade: 9, category: 'Core', is_active: true,
              },
              grades: [
                {
                  id: 20, term: 1, year: 2026, level: 'ME1',
                  source: 'learner', verified_by: null, verified_at: null,
                  created_at: '2026-06-14T10:00:00Z',
                  updated_at: '2026-06-14T10:00:00Z',
                },
              ],
              latest_grade: {
                id: 20, term: 1, year: 2026, level: 'ME1',
                source: 'learner', verified_by: null, verified_at: null,
                created_at: '2026-06-14T10:00:00Z',
                updated_at: '2026-06-14T10:00:00Z',
              },
            },
          ],
        },
        evidence: {
          profile_completion: { status: 'complete', percent: 100, missing_fields: [] },
          academic_evidence: {
            status: 'ready',
            total_subjects: 3,
            subjects_with_evidence: 3,
            total_grade_records: 3,
          },
          assessment: {
            status: 'complete',
            instrument_version: 'riasec-pilot-1.0',
            submitted_at: '2026-06-15T10:30:00Z',
          },
          saved_combination_count: 2,
          plan_status: 'not_started',
          next_action: {
            code: 'compare_combinations',
            title: 'Compare your saved combinations',
            href: '/compare',
          },
        },
        choices: [],
        assessment: {
          id: 1,
          submitted_at: '2026-06-15T10:30:00Z',
          instrument_version: 'riasec-pilot-1.0',
          holland_code: 'IRE',
          scores: { R: 18, I: 22, A: 14, S: 11, E: 16, C: 13 },
          recommendations: [
            { rank: 1, fit_score: 18.25, fit_pct: 73, pathway: { id: 1, name: 'STEM', description: 'Science and tech.' } },
            { rank: 2, fit_score: 14.75, fit_pct: 59, pathway: { id: 2, name: 'Social Sciences', description: 'Humanities.' } },
            { rank: 3, fit_score: 14.65, fit_pct: 59, pathway: { id: 3, name: 'Arts & Sports Science', description: 'Creative arts.' } },
          ],
        },
        counselor: null,
        notifications: [
          {
            id: 1,
            type: 'assessment_submitted',
            message: 'Your RIASEC assessment results are ready.',
            read: false,
            created_at: '2026-06-16T10:00:00Z',
          },
        ],
        interventions: [
          {
            id: 77,
            student: 1,
            student_name: 'Jane Doe',
            category: 'plan',
            action_agreed: 'Review your milestone dates.',
            follow_up_date: '2026-08-06',
            status: 'open',
            learner_visible: true,
            parent_visible: false,
            completed_at: null,
            created_at: '2026-07-29T08:00:00Z',
            updated_at: '2026-07-29T08:00:00Z',
          },
        ],
      },
      error: null,
      message: '',
    })
  }),

  http.get('/api/v1/students/plan/', () => {
    return HttpResponse.json({ data: null, error: null, message: '' })
  }),

  http.get('/api/v1/students/parent-access/', () => {
    return HttpResponse.json({ data: [], error: null, message: '' })
  }),

  http.post('/api/v1/auth/invite-parent/', () => {
    return HttpResponse.json({
      data: null,
      error: null,
      message: 'Invitation sent.',
    })
  }),

  http.get('/api/v1/students/combination-choices/', () => {
    return HttpResponse.json({ data: [], error: null, message: '' })
  }),

  http.post('/api/v1/students/my-subjects/', () => {
    return HttpResponse.json({
      data: { id: 11, subject: { id: 2, name: 'English', code: 'ENG9', grade: 9, category: 'Core', is_active: true }, created_at: '2026-06-14T10:00:00Z' },
      error: null, message: 'Subject added.',
    }, { status: 201 })
  }),

  http.post('/api/v1/students/my-subjects/:id/remove/', () => {
    return HttpResponse.json({ data: null, error: null, message: 'Subject and all grades removed.' })
  }),

  http.get('/api/v1/students/my-subjects/:id/grades/', () => {
    return HttpResponse.json({
      data: [
        { id: 20, term: 1, year: 2026, level: 'ME1', created_at: '2026-06-14T10:00:00Z', updated_at: '2026-06-14T10:00:00Z' },
      ],
      error: null, message: '',
    })
  }),

  http.post('/api/v1/students/my-subjects/:id/grades/', () => {
    return HttpResponse.json({
      data: { id: 21, term: 2, year: 2026, level: 'EE1', created_at: '2026-06-14T10:00:00Z', updated_at: '2026-06-14T10:00:00Z' },
      error: null, message: 'Grade added.',
    }, { status: 201 })
  }),

  // Assessment
  http.get('/api/v1/students/assessment/questions/', () => {
    const questions = Array.from({ length: 30 }, (_, i) => ({
      id: i + 1,
      dimension: (['R', 'I', 'A', 'S', 'E', 'C'] as const)[i % 6],
      text: `Test question ${i + 1}`,
      order: i + 1,
    }))
    return HttpResponse.json({ data: questions, error: null, message: '' })
  }),

  http.post('/api/v1/students/assessment/', () => {
    return HttpResponse.json({
      data: {
        id: 1,
        submitted_at: '2026-06-15T10:30:00Z',
        holland_code: 'IRE',
        scores: { R: 18, I: 22, A: 14, S: 11, E: 16, C: 13 },
        recommendations: [
          { rank: 1, fit_score: 18.25, fit_pct: 73, pathway: { id: 1, name: 'STEM', description: 'Science and tech.' } },
          { rank: 2, fit_score: 14.75, fit_pct: 59, pathway: { id: 2, name: 'Social Sciences', description: 'Humanities.' } },
          { rank: 3, fit_score: 14.65, fit_pct: 59, pathway: { id: 3, name: 'Arts & Sports Science', description: 'Creative arts.' } },
        ],
      },
      error: null,
      message: 'Assessment complete.',
    }, { status: 201 })
  }),

  http.get('/api/v1/students/assessment/', () => {
    return HttpResponse.json({ data: [], error: null, message: '' })
  }),

  http.get('/api/v1/students/assessment/latest/', () => {
    return HttpResponse.json({
      data: {
        id: 1,
        submitted_at: '2026-06-15T10:30:00Z',
        holland_code: 'IRE',
        scores: { R: 18, I: 22, A: 14, S: 11, E: 16, C: 13 },
        recommendations: [
          { rank: 1, fit_score: 18.25, fit_pct: 73, pathway: { id: 1, name: 'STEM', description: 'Science and tech.' } },
          { rank: 2, fit_score: 14.75, fit_pct: 59, pathway: { id: 2, name: 'Social Sciences', description: 'Humanities.' } },
          { rank: 3, fit_score: 14.65, fit_pct: 59, pathway: { id: 3, name: 'Arts & Sports Science', description: 'Creative arts.' } },
        ],
      },
      error: null,
      message: '',
    })
  }),

  // Notifications
  http.get('/api/v1/notifications/', () => {
    return HttpResponse.json({
      data: [
        {
          id: 1,
          type: 'assessment_submitted',
          message: 'Your RIASEC assessment results are ready.',
          read: false,
          created_at: '2026-06-16T10:00:00Z',
        },
        {
          id: 2,
          type: 'counselor_note',
          message: 'Your counselor left a note on your profile.',
          read: true,
          created_at: '2026-06-15T09:00:00Z',
        },
      ],
      error: null,
      message: '',
    })
  }),

  http.get('/api/v1/notifications/unread-count/', () => {
    return HttpResponse.json({ data: { count: 1 }, error: null, message: '' })
  }),

  http.patch('/api/v1/notifications/:id/read/', ({ params }) => {
    return HttpResponse.json({
      data: {
        id: Number(params.id),
        type: 'assessment_submitted',
        message: 'Your RIASEC assessment results are ready.',
        read: true,
        created_at: '2026-06-16T10:00:00Z',
      },
      error: null,
      message: '',
    })
  }),

  http.post('/api/v1/notifications/mark-all-read/', () => {
    return HttpResponse.json({ data: null, error: null, message: 'All notifications marked as read.' })
  }),

  // Dashboard — student counselor
  http.get('/api/v1/students/counselor/', () => {
    return HttpResponse.json({ data: null, error: null, message: '' })
  }),

  http.get('/api/v1/students/interventions/', () => {
    return HttpResponse.json({
      data: [
        {
          id: 77,
          student: 1,
          student_name: 'Jane Doe',
          category: 'plan',
          action_agreed: 'Review your milestone dates.',
          follow_up_date: '2026-08-06',
          status: 'open',
          learner_visible: true,
          parent_visible: false,
          completed_at: null,
          created_at: '2026-07-29T08:00:00Z',
          updated_at: '2026-07-29T08:00:00Z',
        },
      ],
      error: null,
      message: '',
    })
  }),

  // Dashboard — counselor views
  http.get('/api/v1/counselors/students/', () => {
    return HttpResponse.json({
      data: [
        {
          id: 5, first_name: 'Jane', last_name: 'Doe', grade: 9,
          county: 'kiambu', photo_url: null, top_pathway: 'STEM',
          fit_pct: 73, quiz_status: 'done', last_active: '2026-06-17T08:00:00Z',
          needs_attention: true,
          attention_reasons: [
            {
              code: 'academic_evidence_missing',
              label: 'Academic evidence incomplete',
              guidance: 'Review the enrolled subjects and add missing grade evidence.',
            },
          ],
        },
        {
          id: 6, first_name: 'Brian', last_name: 'Kamau', grade: 10,
          county: 'nyeri', photo_url: null, top_pathway: null,
          fit_pct: null, quiz_status: 'pending', last_active: null,
          needs_attention: true,
          attention_reasons: [
            {
              code: 'assessment_missing',
              label: 'Interest assessment missing',
              guidance: 'Invite the learner to complete the interest assessment.',
            },
            {
              code: 'no_plan',
              label: 'No learner plan',
              guidance: 'Support the learner to turn a provisional choice into a plan.',
            },
          ],
        },
      ],
      error: null, message: '',
    })
  }),

  http.get('/api/v1/counselors/students/:id/', () => {
    return HttpResponse.json({
      data: {
        student: {
          id: 5, email: 'jane@test.com', first_name: 'Jane', last_name: 'Doe',
          grade: 9, county: 'kiambu', school: 'Kiambu High', photo_url: null,
          bio: 'I love science', career_interests: 'Medicine', created_at: '2026-06-01T10:00:00Z',
        },
        riasec_result: {
          id: 1, submitted_at: '2026-06-15T10:30:00Z', holland_code: 'IRE',
          scores: { R: 18, I: 22, A: 14, S: 11, E: 16, C: 13 },
          recommendations: [
            { rank: 1, fit_score: 18.25, fit_pct: 73, pathway: { id: 1, name: 'STEM', description: 'Science and technology.' } },
            { rank: 2, fit_score: 14.75, fit_pct: 59, pathway: { id: 2, name: 'Social Sciences', description: 'Humanities.' } },
            { rank: 3, fit_score: 14.65, fit_pct: 59, pathway: { id: 3, name: 'Arts & Sports Science', description: 'Creative arts.' } },
          ],
        },
        grades: [
          { id: 20, subject_name: 'Mathematics', subject_code: 'MTH9', term: 1, year: 2026, level: 'ME1', created_at: '2026-06-14T10:00:00Z', updated_at: '2026-06-14T10:00:00Z' },
        ],
        notes_count: 2,
        attention_reasons: [
          {
            code: 'academic_evidence_missing',
            label: 'Academic evidence incomplete',
            guidance: 'Review the enrolled subjects and add missing grade evidence.',
          },
        ],
        evidence_summary: {
          academic: {
            status: 'in_progress',
            total_subjects: 2,
            subjects_with_evidence: 1,
            total_grade_records: 1,
          },
          assessment: { status: 'complete' },
        },
        combination_choices: [
          {
            id: 12,
            status: 'provisional',
            learner_reason: 'I enjoy practical science.',
            code: 'ST1042',
            title: 'Agriculture, Biology & Chemistry',
            pathway: 'STEM',
            track: 'Pure Sciences',
            subjects: ['Agriculture', 'Biology', 'Chemistry'],
          },
        ],
        plan: {
          status: 'ready_for_review',
          learner_reason: 'This route connects to my interests.',
          milestones: [
            {
              id: 1,
              title: 'Review two pilot schools',
              due_date: '2026-09-15',
              is_complete: false,
            },
          ],
        },
        interventions: [
          {
            id: 91,
            student: 5,
            student_name: 'Jane Doe',
            category: 'academic_evidence',
            action_agreed: 'Bring the latest mathematics evidence.',
            follow_up_date: '2026-08-04',
            status: 'open',
            learner_visible: true,
            parent_visible: true,
            completed_at: null,
            created_at: '2026-07-29T09:00:00Z',
            updated_at: '2026-07-29T09:00:00Z',
          },
        ],
      },
      error: null, message: '',
    })
  }),

  http.put('/api/v1/counselors/students/:id/plan-review/', async ({ request }) => {
    const body = await request.json() as { reviewed: boolean }
    return HttpResponse.json({
      data: {
        id: 1,
        status: body.reviewed ? 'reviewed' : 'ready_for_review',
        reviewed_at: body.reviewed ? '2026-07-30T16:00:00Z' : null,
      },
      error: null,
      message: body.reviewed
        ? 'Learner plan marked reviewed.'
        : 'Learner plan reopened for review.',
    })
  }),

  http.get('/api/v1/counselors/stats/', () => {
    return HttpResponse.json({
      data: {
        total_students: 12,
        assessments_done: 8,
        students_needing_attention: 4,
        follow_ups_due: 2,
        journeys_reviewed: 3,
        notes_written: 23,
      },
      error: null, message: '',
    })
  }),

  http.get('/api/v1/counselors/notes/', () => {
    return HttpResponse.json({
      data: [
        { id: 1, student: 5, student_name: 'Jane Doe', body: 'Great progress in math.', created_at: '2026-06-16T10:00:00Z', updated_at: '2026-06-16T10:00:00Z' },
        { id: 2, student: 5, student_name: 'Jane Doe', body: 'Needs help with science.', created_at: '2026-06-15T10:00:00Z', updated_at: '2026-06-15T10:00:00Z' },
      ],
      error: null, message: '',
    })
  }),

  http.post('/api/v1/counselors/notes/', async ({ request }) => {
    const body = await request.json() as { student_id: number; body: string }
    return HttpResponse.json({
      data: { id: 99, student: body.student_id, student_name: 'Jane Doe', body: body.body, created_at: '2026-06-17T10:00:00Z', updated_at: '2026-06-17T10:00:00Z' },
      error: null, message: 'Note saved for Jane.',
    }, { status: 201 })
  }),

  http.patch('/api/v1/counselors/notes/:id/', async ({ request }) => {
    const body = await request.json() as { body: string }
    return HttpResponse.json({
      data: { id: 1, student: 5, student_name: 'Jane Doe', body: body.body, created_at: '2026-06-16T10:00:00Z', updated_at: '2026-06-17T10:00:00Z' },
      error: null, message: 'Note updated.',
    })
  }),

  http.delete('/api/v1/counselors/notes/:id/', () => {
    return HttpResponse.json({
      data: null, error: null, message: 'Note removed.',
    })
  }),

  http.get('/api/v1/counselors/interventions/', () => {
    return HttpResponse.json({
      data: [
        {
          id: 91,
          student: 5,
          student_name: 'Jane Doe',
          category: 'academic_evidence',
          action_agreed: 'Bring the latest mathematics evidence.',
          follow_up_date: '2026-08-04',
          status: 'open',
          learner_visible: true,
          parent_visible: true,
          completed_at: null,
          created_at: '2026-07-29T09:00:00Z',
          updated_at: '2026-07-29T09:00:00Z',
        },
      ],
      error: null,
      message: '',
    })
  }),

  // Dashboard — parent children
  http.post('/api/v1/counselors/interventions/', async ({ request }) => {
    const body = await request.json() as {
      student_id: number
      category: string
      action_agreed: string
      follow_up_date: string | null
      learner_visible: boolean
      parent_visible: boolean
    }
    return HttpResponse.json({
      data: {
        id: 92,
        student: body.student_id,
        student_name: 'Jane Doe',
        category: body.category,
        action_agreed: body.action_agreed,
        follow_up_date: body.follow_up_date,
        status: 'open',
        learner_visible: body.learner_visible,
        parent_visible: body.parent_visible,
        completed_at: null,
        created_at: '2026-07-30T09:00:00Z',
        updated_at: '2026-07-30T09:00:00Z',
      },
      error: null,
      message: 'Intervention created.',
    }, { status: 201 })
  }),

  http.patch('/api/v1/counselors/interventions/:id/', async ({ params, request }) => {
    const body = await request.json() as {
      status?: 'open' | 'completed'
      category?: string
      action_agreed?: string
      follow_up_date?: string | null
      learner_visible?: boolean
      parent_visible?: boolean
    }
    return HttpResponse.json({
      data: {
        id: Number(params.id),
        student: 5,
        student_name: 'Jane Doe',
        category: body.category ?? 'academic_evidence',
        action_agreed: body.action_agreed ?? 'Bring the latest mathematics evidence.',
        follow_up_date: body.follow_up_date ?? '2026-08-04',
        status: body.status ?? 'open',
        learner_visible: body.learner_visible ?? true,
        parent_visible: body.parent_visible ?? true,
        completed_at: body.status === 'completed' ? '2026-07-30T09:30:00Z' : null,
        created_at: '2026-07-29T09:00:00Z',
        updated_at: '2026-07-30T09:30:00Z',
      },
      error: null,
      message: 'Intervention updated.',
    })
  }),

  http.get('/api/v1/parents/children/', () => {
    return HttpResponse.json({
      data: [
        {
          id: 10,
          first_name: 'Tom',
          last_name: 'Doe',
          grade: 9,
          county: 'kiambu',
          photo_url: null,
          quiz_status: 'done',
          subject_count: 5,
          counselor_assigned: true,
          last_active: '2026-06-18T10:00:00Z',
          top_pathway: 'Engineering',
          access_status: 'active',
          next_action: {
            code: 'review_plan',
            title: 'Review your plan and next milestone',
          },
          provisional_combination: {
            id: 1,
            code: 'ST1042',
            title: 'Agriculture, Biology & Chemistry',
            pathway: 'STEM',
            track: 'Pure Sciences',
          },
          plan_status: 'draft',
          plan_progress: { completed: 1, total: 3 },
          upcoming_milestone: {
            id: 1,
            title: 'Review two pilot schools',
            due_date: '2026-09-15',
          },
          conversation_prompt: 'How can I support your next plan milestone?',
        },
        {
          id: 11,
          first_name: 'Alice',
          last_name: 'Doe',
          grade: 10,
          county: 'kiambu',
          photo_url: null,
          quiz_status: 'pending',
          subject_count: 3,
          counselor_assigned: false,
          last_active: '2026-06-17T08:00:00Z',
          top_pathway: null,
          access_status: 'active',
          next_action: {
            code: 'complete_interest_assessment',
            title: 'Complete your interest assessment',
          },
          provisional_combination: null,
          plan_status: 'not_started',
          plan_progress: { completed: 0, total: 0 },
          upcoming_milestone: null,
          conversation_prompt: 'Which activities make you feel curious or energized?',
        },
      ],
      error: null,
      message: '',
    })
  }),

  // Parent child detail
  http.get('/api/v1/parents/children/:id/', () => {
    return HttpResponse.json({
      data: {
        profile: {
          id: 10,
          first_name: 'Tom',
          last_name: 'Doe',
          email: 'tom@test.com',
          county: 'kiambu',
          grade: 9,
          mode: 'school_linked',
          bio: 'Loves math and science',
          date_of_birth: '2010-05-15',
          career_interests: 'Engineering, Medicine',
          photo_url: null,
        },
        subjects: [
          {
            id: 1,
            name: 'Mathematics',
            code: 'MAT0019',
            category: 'Core',
            grades: [
              { id: 1, term: 1, year: 2026, level: 'ME1' },
              { id: 2, term: 2, year: 2026, level: 'EE1' },
            ],
          },
          {
            id: 2,
            name: 'English',
            code: 'ENG0019',
            category: 'Core',
            grades: [{ id: 3, term: 1, year: 2026, level: 'AE1' }],
          },
        ],
        assessment: {
          id: 1,
          submitted_at: '2026-06-15T10:00:00Z',
          holland_code: 'RIA',
          scores: { R: 25, I: 22, A: 18, S: 14, E: 12, C: 10 },
          recommendations: [
            {
              rank: 1,
              fit_score: 85,
              fit_pct: 90,
              pathway: { id: 1, name: 'Engineering', description: 'Build and design systems' },
            },
            {
              rank: 2,
              fit_score: 72,
              fit_pct: 78,
              pathway: { id: 2, name: 'Medicine', description: 'Healthcare and life sciences' },
            },
            {
              rank: 3,
              fit_score: 65,
              fit_pct: 70,
              pathway: { id: 3, name: 'Architecture', description: 'Design physical spaces' },
            },
          ],
        },
        academic_readiness: {
          status: 'in_progress',
          total_subjects: 2,
          subjects_with_evidence: 2,
          total_grade_records: 3,
        },
        provisional_combination: {
          id: 1,
          code: 'ST1042',
          title: 'Agriculture, Biology & Chemistry',
          pathway: 'STEM',
          track: 'Pure Sciences',
          subjects: ['Agriculture', 'Biology', 'Chemistry'],
        },
        plan: {
          status: 'draft',
          learner_reason: 'I enjoy practical science and want to explore agriculture.',
          milestones: [
            {
              id: 1,
              title: 'Review two pilot schools',
              due_date: '2026-09-15',
              is_complete: false,
              completed_at: null,
            },
            {
              id: 2,
              title: 'Discuss subject strengths',
              due_date: null,
              is_complete: true,
              completed_at: '2026-07-20T10:00:00Z',
            },
          ],
        },
        counselor: {
          id: 5,
          first_name: 'Dr',
          last_name: 'Smith',
          email: 'drsmith@school.com',
        },
        latest_note: {
          body: 'Tom is showing great progress in mathematics this term. Keep encouraging him!',
          created_at: '2026-06-15T14:30:00Z',
          updated_at: '2026-06-15T14:30:00Z',
        },
        parent_visible_notes: [
          {
            body: 'Tom is showing great progress in mathematics this term. Keep encouraging him!',
            created_at: '2026-06-15T14:30:00Z',
            updated_at: '2026-06-15T14:30:00Z',
          },
        ],
        interventions: [
          {
            id: 81,
            student: 10,
            student_name: 'Tom Doe',
            category: 'plan',
            action_agreed: 'Discuss the reviewed learner plan.',
            follow_up_date: '2026-08-08',
            status: 'open',
            learner_visible: true,
            parent_visible: true,
            completed_at: null,
            created_at: '2026-07-29T08:00:00Z',
            updated_at: '2026-07-29T08:00:00Z',
          },
        ],
      },
      error: null,
      message: '',
    })
  }),

  // School Admin handlers
  http.get('/api/v1/school-admin/school/', () => {
    return HttpResponse.json({
      data: {
        id: 1, name: 'Starehe Boys Centre', county: 'nairobi', school_code: 'NAI001',
        logo_url: null, phone: '+254712345678', email: 'info@starehe.ac.ke',
        student_count: 24, counselor_count: 3,
      },
      error: null, message: '',
    })
  }),

  http.patch('/api/v1/school-admin/school/', () => {
    return HttpResponse.json({
      data: {
        id: 1, name: 'Starehe Boys Centre', county: 'nairobi', school_code: 'NAI001',
        logo_url: null, phone: '+254712345678', email: 'info@starehe.ac.ke',
        student_count: 24, counselor_count: 3,
      },
      error: null, message: 'School profile updated.',
    })
  }),

  http.post('/api/v1/school-admin/school/logo/', () => {
    return HttpResponse.json({
      data: { logo_url: 'https://storage.example.com/school-logos/school_1.png' },
      error: null, message: 'School logo updated.',
    })
  }),

  http.post('/api/v1/school-admin/school/logo/remove/', () => {
    return HttpResponse.json({ data: null, error: null, message: 'Logo removed.' })
  }),

  http.get('/api/v1/school-admin/counselors/', () => {
    return HttpResponse.json({
      data: [
        { id: 10, first_name: 'Alice', last_name: 'Wanjiku', email: 'alice@school.co.ke', student_count: 8, joined_at: '2026-01-15T10:00:00Z' },
        { id: 11, first_name: 'Bob', last_name: 'Ochieng', email: 'bob@school.co.ke', student_count: 12, joined_at: '2026-03-01T10:00:00Z' },
      ],
      error: null, message: '',
    })
  }),

  http.post('/api/v1/school-admin/counselors/add/', () => {
    return HttpResponse.json({
      data: { id: 12, email: 'new@school.co.ke' },
      error: null, message: 'New Counselor added to Starehe Boys Centre.',
    })
  }),

  http.post(/\/api\/v1\/school-admin\/counselors\/\d+\/remove\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Counselor removed.' })
  }),

  http.get('/api/v1/school-admin/students/', () => {
    return HttpResponse.json({
      data: [
        { id: 20, first_name: 'Jane', last_name: 'Muthoni', email: 'jane@student.co.ke', grade: 9, photo_url: null, quiz_status: 'done', school_membership_status: 'active', counselor_id: 10, counselor_name: 'Alice Wanjiku' },
        { id: 21, first_name: 'Kevin', last_name: 'Otieno', email: 'kevin@student.co.ke', grade: 10, photo_url: null, quiz_status: 'pending', school_membership_status: 'active', counselor_id: null, counselor_name: null },
      ],
      error: null, message: '',
    })
  }),

  http.get('/api/v1/school-admin/membership-requests/', () => {
    return HttpResponse.json({
      data: [
        {
          student_id: 22,
          first_name: 'Mary',
          last_name: 'Wanjiru',
          email: 'mary@student.co.ke',
          grade: 10,
          requested_at: '2026-07-30T08:00:00+00:00',
        },
      ],
      error: null,
      message: '',
    })
  }),

  http.put('/api/v1/school-admin/membership-requests/:studentId/decision/', ({ params }) => {
    return HttpResponse.json({
      data: {
        student_id: Number(params.studentId),
        school_membership_status: 'active',
      },
      error: null,
      message: 'Learner school link approved.',
    })
  }),

  http.get('/api/v1/school-admin/stats/', () => {
    return HttpResponse.json({
      data: {
        total_students: 24,
        total_counselors: 3,
        assessed: 18,
        unassigned: 6,
        pending_memberships: 2,
        evidence_complete: 16,
        choices_saved: 14,
        plans_created: 10,
        reviews_completed: 7,
        offerings_count: 12,
        offerings_configured: true,
        counselor_workload: [
          { counselor_id: 10, counselor_name: 'Alice Wanjiku', student_count: 9 },
          { counselor_id: 11, counselor_name: 'Bob Ochieng', student_count: 8 },
        ],
      },
      error: null, message: '',
    })
  }),

  http.post('/api/v1/school-admin/assignments/', () => {
    return HttpResponse.json({
      data: { id: 100, student_id: 21, counselor_id: 10 },
      error: null, message: 'Kevin assigned to Alice Wanjiku.',
    })
  }),

  http.post('/api/v1/school-admin/assignments/bulk/', async ({ request }) => {
    const body = await request.json() as {
      student_ids: number[]
      counselor_id: number
    }
    return HttpResponse.json({
      data: {
        assigned_count: body.student_ids.length,
        counselor_id: body.counselor_id,
        student_ids: body.student_ids,
      },
      error: null,
      message: `${body.student_ids.length} learners assigned.`,
    }, { status: 201 })
  }),

  http.post(/\/api\/v1\/school-admin\/assignments\/\d+\/remove\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Assignment removed.' })
  }),

  // System Admin
  http.get('/api/v1/system-admin/dashboard/', () => {
    return HttpResponse.json({
      data: {
        users_by_role: { student: 45, counselor: 8, school_admin: 3, parent: 20, system_admin: 1 },
        schools_by_county: { kiambu: 4, nyeri: 3, muranga: 2, kirinyaga: 1, nyandarua: 1 },
        total_schools: 11,
        registered_learners: 45,
        learners_by_county: { kiambu: 14, nyeri: 10, muranga: 9, kirinyaga: 6, nyandarua: 6 },
        verified_learners: 38,
        pending_school_links: 5,
        assignment_coverage: { assigned: 28, eligible: 34, percent: 82 },
        plans_completed: 17,
        framework: {
          code: 'CBC-SS-PILOT-2026',
          title: 'CBC Senior School Pilot Catalogue 2026',
          source_url: 'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
          effective_date: '2026-01-01',
        },
        recent_signups: 7,
        recent_audit: [
          { id: 1, action: 'school_created', target_type: 'school', target_id: 1, actor_email: 'admin@test.com', actor_name: 'Admin User', created_at: '2026-06-19T10:00:00Z' },
          { id: 2, action: 'invite_sent', target_type: 'user', target_id: 0, actor_email: 'admin@test.com', actor_name: 'Admin User', created_at: '2026-06-19T09:00:00Z' },
        ],
      },
      error: null,
      message: '',
    })
  }),

  http.get('/api/v1/system-admin/catalogue/', () => {
    return HttpResponse.json({
      data: {
        framework: {
          id: 1,
          code: 'CBC-SS-PILOT-2026',
          title: 'CBC Senior School Pilot Catalogue 2026',
          description: 'Curated five-county pilot catalogue.',
          source_url: 'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
          effective_date: '2026-01-01',
          is_active: true,
        },
        combinations: [
          {
            id: 1,
            code: 'ST1042',
            title: 'Advanced Mathematics, Physics, Chemistry',
            description: 'Pure sciences combination.',
            related_routes: ['Engineering'],
            is_active: true,
            track: {
              id: 1,
              code: 'PURE-SCIENCES',
              name: 'Pure Sciences',
              is_active: true,
              pathway: { id: 1, name: 'STEM' },
            },
            subjects: [
              { id: 1, code: 'ADV-MATH', name: 'Advanced Mathematics' },
              { id: 2, code: 'PHYS', name: 'Physics' },
              { id: 3, code: 'CHEM', name: 'Chemistry' },
            ],
            active_school_count: 2,
            learner_choice_count: 4,
          },
          {
            id: 2,
            code: 'ST1043',
            title: 'Biology, Chemistry, Agriculture',
            description: 'Applied sciences combination.',
            related_routes: ['Agriculture'],
            is_active: false,
            track: {
              id: 2,
              code: 'APPLIED-SCIENCES',
              name: 'Applied Sciences',
              is_active: true,
              pathway: { id: 1, name: 'STEM' },
            },
            subjects: [
              { id: 4, code: 'BIO', name: 'Biology' },
              { id: 3, code: 'CHEM', name: 'Chemistry' },
              { id: 5, code: 'AGRI', name: 'Agriculture' },
            ],
            active_school_count: 0,
            learner_choice_count: 1,
          },
        ],
      },
      error: null,
      message: '',
    })
  }),

  http.patch(/\/api\/v1\/system-admin\/catalogue\/combinations\/\d+\//, async ({ request }) => {
    const body = await request.json() as { is_active: boolean }
    return HttpResponse.json({
      data: {
        id: 1,
        code: 'ST1042',
        title: 'Advanced Mathematics, Physics, Chemistry',
        description: 'Pure sciences combination.',
        related_routes: ['Engineering'],
        is_active: body.is_active,
        track: {
          id: 1,
          code: 'PURE-SCIENCES',
          name: 'Pure Sciences',
          is_active: true,
          pathway: { id: 1, name: 'STEM' },
        },
        subjects: [
          { id: 1, code: 'ADV-MATH', name: 'Advanced Mathematics' },
          { id: 2, code: 'PHYS', name: 'Physics' },
          { id: 3, code: 'CHEM', name: 'Chemistry' },
        ],
        active_school_count: 2,
        learner_choice_count: 4,
      },
      error: null,
      message: 'Combination status updated.',
    })
  }),

  http.get('/api/v1/system-admin/schools/', () => {
    return HttpResponse.json({
      data: {
        results: [
          { id: 1, name: 'Starehe Boys Centre', county: 'kiambu', school_code: 'KIA001', phone: '+254712345678', email: 'info@starehe.ac.ke', logo_url: null, is_active: true, student_count: 24, counselor_count: 3 },
          { id: 2, name: 'Alliance Girls', county: 'kiambu', school_code: 'KIA002', phone: '', email: '', logo_url: null, is_active: true, student_count: 30, counselor_count: 2 },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      },
      error: null,
      message: '',
    })
  }),

  http.post('/api/v1/system-admin/schools/', async ({ request }) => {
    const body = await request.json() as { name: string; county: string; school_code: string }
    return HttpResponse.json({
      data: { id: 99, name: body.name, county: body.county, school_code: body.school_code, phone: '', email: '', logo_url: null, is_active: true },
      error: null,
      message: `${body.name} created.`,
    }, { status: 201 })
  }),

  http.get(/\/api\/v1\/system-admin\/schools\/\d+\//, () => {
    return HttpResponse.json({
      data: {
        id: 1, name: 'Starehe Boys Centre', county: 'kiambu', school_code: 'KIA001', phone: '+254712345678', email: 'info@starehe.ac.ke', logo_url: null, is_active: true, student_count: 24, counselor_count: 3,
        counselors: [
          { id: 10, first_name: 'Alice', last_name: 'Wanjiku', email: 'alice@school.co.ke', student_count: 8 },
        ],
        recent_students: [
          { id: 20, first_name: 'Jane', last_name: 'Muthoni', grade: 9, created_at: '2026-06-15T10:00:00Z' },
        ],
      },
      error: null,
      message: '',
    })
  }),

  http.patch(/\/api\/v1\/system-admin\/schools\/\d+\//, () => {
    return HttpResponse.json({
      data: { id: 1, name: 'Updated School', county: 'kiambu', school_code: 'KIA001', phone: '', email: '', logo_url: null, is_active: true },
      error: null,
      message: 'School updated.',
    })
  }),

  http.post(/\/api\/v1\/system-admin\/schools\/\d+\/deactivate\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'School has been deactivated.' })
  }),

  http.post(/\/api\/v1\/system-admin\/schools\/\d+\/activate\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'School has been activated.' })
  }),

  http.get('/api/v1/system-admin/users/', () => {
    return HttpResponse.json({
      data: {
        results: [
          { id: 1, first_name: 'Jane', last_name: 'Doe', email: 'jane@test.com', role: 'student', county: 'kiambu', school_name: 'Starehe Boys', is_active: true, is_email_verified: true, created_at: '2026-06-01T10:00:00Z' },
          { id: 2, first_name: 'Bob', last_name: 'Smith', email: 'bob@test.com', role: 'counselor', county: 'nyeri', school_name: 'Alliance Girls', is_active: true, is_email_verified: true, created_at: '2026-06-05T10:00:00Z' },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      },
      error: null,
      message: '',
    })
  }),

  http.get(/\/api\/v1\/system-admin\/users\/\d+\//, () => {
    return HttpResponse.json({
      data: {
        id: 1, first_name: 'Jane', last_name: 'Doe', email: 'jane@test.com', role: 'student', county: 'kiambu', school_id: 1, school_name: 'Starehe Boys', is_active: true, is_email_verified: true, created_at: '2026-06-01T10:00:00Z', last_login: '2026-06-19T08:00:00Z', grade: 9, mode: 'school_linked', has_assessment: true,
      },
      error: null,
      message: '',
    })
  }),

  http.post(/\/api\/v1\/system-admin\/users\/\d+\/deactivate\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'User has been deactivated.' })
  }),

  http.post(/\/api\/v1\/system-admin\/users\/\d+\/activate\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'User has been activated.' })
  }),

  http.get('/api/v1/system-admin/audit-logs/', () => {
    return HttpResponse.json({
      data: {
        results: [
          { id: 1, actor_email: 'admin@test.com', actor_name: 'Admin User', action: 'school_created', target_type: 'school', target_id: 1, details: { name: 'Starehe Boys' }, ip_address: '192.168.1.1', created_at: '2026-06-19T10:00:00Z' },
          { id: 2, actor_email: 'admin@test.com', actor_name: 'Admin User', action: 'invite_sent', target_type: 'user', target_id: 0, details: { email: 'new@test.com', role: 'counselor' }, ip_address: '192.168.1.1', created_at: '2026-06-19T09:00:00Z' },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      },
      error: null,
      message: '',
    })
  }),

  // Guidance catalogue
  http.get('/api/v1/guidance/framework/current/', () => {
    return HttpResponse.json({
      data: {
        id: 1,
        code: 'CBC-SS-PILOT-2026',
        title: 'CBC Senior School Pilot Catalogue 2026',
        description: 'Curated five-county pilot catalogue.',
        source_url: 'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
        effective_date: '2026-01-01',
        is_active: true,
      },
      error: null,
      message: '',
    })
  }),

  http.get('/api/v1/guidance/pathways/', () => {
    const pathwayTracks = [
      ['STEM', ['PURE-SCIENCES', 'APPLIED-SCIENCES']],
      ['Social Sciences', ['HUMANITIES-BUSINESS']],
      ['Arts & Sports Science', ['ARTS']],
    ] as const
    const pathways = pathwayTracks.map(([name, trackCodes], index) => ({
      id: index + 1,
      name,
      description: `${name} pathway`,
      tracks: trackCodes.map((trackCode, trackIndex) => ({
        id: (index * 10) + trackIndex + 1,
        code: trackCode,
        name: trackCode
          .toLowerCase()
          .replace(/-/g, ' ')
          .replace(/\b\w/g, character => character.toUpperCase()),
        description: 'Pilot track',
        is_active: true,
        pathway: { id: index + 1, name, description: `${name} pathway` },
      })),
    }))
    return HttpResponse.json({ data: pathways, error: null, message: '' })
  }),

  http.get('/api/v1/guidance/combinations/', ({ request }) => {
    const url = new URL(request.url)
    const hasExpectedFilters = (
      url.searchParams.get('pathway') === 'STEM'
      && url.searchParams.get('county') === 'kiambu'
      && url.searchParams.get('search') === 'science'
    )
    void hasExpectedFilters
    return HttpResponse.json({
      data: [{
        id: 1,
        code: 'ST1042',
        title: 'Agriculture, Biology & Chemistry',
        description: 'Curated pilot option.',
        related_routes: ['Agricultural science', 'Biological science', 'Laboratory technology'],
        framework: {
          code: 'CBC-SS-PILOT-2026',
          title: 'CBC Senior School Pilot Catalogue 2026',
          source_url: 'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
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
        offered_schools: [],
      }],
      error: null,
      message: '',
    })
  }),

  http.get(/\/api\/v1\/guidance\/combinations\/\d+\//, () => {
    return HttpResponse.json({
      data: {
        id: 1,
        code: 'ST1042',
        title: 'Agriculture, Biology & Chemistry',
        description: 'Curated pilot option.',
        related_routes: ['Agricultural science', 'Biological science', 'Laboratory technology'],
        framework: {
          code: 'CBC-SS-PILOT-2026',
          title: 'CBC Senior School Pilot Catalogue 2026',
          source_url: 'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
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
        offered_schools: [],
      },
      error: null,
      message: '',
    })
  }),

  http.get('/api/v1/students/combination-choices/', () => {
    return HttpResponse.json({ data: [], error: null, message: '' })
  }),

  http.post('/api/v1/students/combination-choices/', async ({ request }) => {
    const body = await request.json() as { combination_id: number; learner_reason?: string }
    return HttpResponse.json({
      data: {
        id: 11,
        status: 'saved',
        learner_reason: body.learner_reason ?? '',
        created_at: '2026-07-30T10:00:00Z',
        updated_at: '2026-07-30T10:00:00Z',
        combination: {
          id: body.combination_id,
          code: 'ST1042',
          title: 'Agriculture, Biology & Chemistry',
          description: 'Curated pilot option.',
          related_routes: ['Agricultural science', 'Biological science', 'Laboratory technology'],
          framework: {
            code: 'CBC-SS-PILOT-2026',
            title: 'CBC Senior School Pilot Catalogue 2026',
            source_url: 'https://selection-placement.kemis.go.ke/uploads/catalogue.pdf',
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
          offered_schools: [],
        },
      },
      error: null,
      message: 'Combination saved.',
    }, { status: 201 })
  }),

  http.delete(/\/api\/v1\/students\/combination-choices\/\d+\//, () => {
    return HttpResponse.json(
      { data: null, error: null, message: 'Saved combination removed.' },
      { status: 200 },
    )
  }),

  http.put(/\/api\/v1\/students\/combination-choices\/\d+\/provisional\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Provisional combination updated.' })
  }),

  http.get('/api/v1/school-admin/offerings/', () => {
    return HttpResponse.json({
      data: {
        school: { id: 1, school_code: 'PILOT-KIA-001', name: 'Pilot School', county: 'kiambu' },
        combination_ids: [1],
        offerings: [],
      },
      error: null,
      message: '',
    })
  }),

  http.put('/api/v1/school-admin/offerings/', async ({ request }) => {
    const body = await request.json() as { combination_ids: number[] }
    return HttpResponse.json({
      data: {
        school: { id: 1, school_code: 'PILOT-KIA-001', name: 'Pilot School', county: 'kiambu' },
        combination_ids: body.combination_ids,
        offerings: [],
      },
      error: null,
      message: 'School offerings updated.',
    })
  }),

  // Reports
  http.get(/\/api\/v1\/reports\/student\/\d+\/pdf\//, () => {
    const pdfContent = '%PDF-1.4 mock report content'
    return new HttpResponse(pdfContent, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="smarta-shauri-report-Test-Student-2026-06-20.pdf"',
      },
    })
  }),
]
