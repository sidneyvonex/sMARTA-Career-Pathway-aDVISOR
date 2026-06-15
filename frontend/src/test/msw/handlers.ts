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
]
