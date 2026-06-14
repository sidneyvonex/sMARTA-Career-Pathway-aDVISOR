import api from '../lib/axios'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: 'student' | 'counselor' | 'school_admin' | 'parent' | 'system_admin'
  county: string | null
  is_email_verified: boolean
}

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  county: string
  grade: number
  role: 'student'
  school_code?: string
}

export const authApi = {
  register: (data: RegisterPayload) => api.post('/auth/register/', data),
  login: (email: string, password: string) => api.post('/auth/login/', { email, password }),
  logout: () => api.post('/auth/logout/'),
  me: () => api.get<{ data: { user: User } }>('/auth/me/'),
  verifyEmail: (token: string) => api.get(`/auth/verify-email/?token=${token}`),
  resendVerification: () => api.post('/auth/resend-verification/'),
  requestPasswordReset: (email: string) => api.post('/auth/password-reset/', { email }),
  confirmPasswordReset: (token: string, password: string) =>
    api.post('/auth/password-reset/confirm/', { token, password }),
  acceptInvite: (payload: {
    token: string
    password: string
    first_name: string
    last_name: string
    county: string
  }) => api.post('/auth/accept-invite/', payload),
}
