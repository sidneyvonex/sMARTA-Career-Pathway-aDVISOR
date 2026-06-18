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
        county: 'kiambu', grade: 9, mode: 'self_guided',
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
        county: 'kiambu', grade: 9, mode: 'self_guided',
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
        { id: 1, name: 'Mathematics', code: `MTH${grade}`, grade, category: 'Core' },
        { id: 2, name: 'English', code: `ENG${grade}`, grade, category: 'Core' },
      ],
      error: null, message: '',
    })
  }),

  http.get('/api/v1/students/my-subjects/', () => {
    return HttpResponse.json({
      data: [
        { id: 10, subject: { id: 1, name: 'Mathematics', code: 'MTH9', grade: 9, category: 'Core' }, created_at: '2026-06-14T10:00:00Z' },
      ],
      error: null, message: '',
    })
  }),

  http.post('/api/v1/students/my-subjects/', () => {
    return HttpResponse.json({
      data: { id: 11, subject: { id: 2, name: 'English', code: 'ENG9', grade: 9, category: 'Core' }, created_at: '2026-06-14T10:00:00Z' },
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

  // Dashboard — counselor views
  http.get('/api/v1/counselors/students/', () => {
    return HttpResponse.json({
      data: [
        {
          id: 5, first_name: 'Jane', last_name: 'Doe', grade: 9,
          county: 'kiambu', photo_url: null, top_pathway: 'STEM',
          fit_pct: 73, quiz_status: 'done', last_active: '2026-06-17T08:00:00Z',
        },
        {
          id: 6, first_name: 'Brian', last_name: 'Kamau', grade: 10,
          county: 'nyeri', photo_url: null, top_pathway: null,
          fit_pct: null, quiz_status: 'pending', last_active: null,
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
      },
      error: null, message: '',
    })
  }),

  http.get('/api/v1/counselors/stats/', () => {
    return HttpResponse.json({
      data: { total_students: 12, assessments_done: 8, students_needing_attention: 4, notes_written: 23 },
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

  // Dashboard — parent children
  http.get('/api/v1/parents/children/', () => {
    return HttpResponse.json({ data: [], error: null, message: '' })
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
        { id: 20, first_name: 'Jane', last_name: 'Muthoni', email: 'jane@student.co.ke', grade: 9, photo_url: null, quiz_status: 'done', counselor_id: 10, counselor_name: 'Alice Wanjiku' },
        { id: 21, first_name: 'Kevin', last_name: 'Otieno', email: 'kevin@student.co.ke', grade: 10, photo_url: null, quiz_status: 'pending', counselor_id: null, counselor_name: null },
      ],
      error: null, message: '',
    })
  }),

  http.get('/api/v1/school-admin/stats/', () => {
    return HttpResponse.json({
      data: { total_students: 24, total_counselors: 3, assessed: 18, unassigned: 6 },
      error: null, message: '',
    })
  }),

  http.post('/api/v1/school-admin/assignments/', () => {
    return HttpResponse.json({
      data: { id: 100, student_id: 21, counselor_id: 10 },
      error: null, message: 'Kevin assigned to Alice Wanjiku.',
    })
  }),

  http.post(/\/api\/v1\/school-admin\/assignments\/\d+\/remove\//, () => {
    return HttpResponse.json({ data: null, error: null, message: 'Assignment removed.' })
  }),
]
