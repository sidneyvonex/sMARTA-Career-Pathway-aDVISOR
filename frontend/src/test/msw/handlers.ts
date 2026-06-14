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
]
