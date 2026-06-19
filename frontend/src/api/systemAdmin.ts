import api from '../lib/axios'

export interface DashboardData {
  users_by_role: Record<string, number>
  schools_by_county: Record<string, number>
  total_schools: number
  recent_signups: number
  recent_audit: AuditEntry[]
}

export interface SchoolItem {
  id: number
  name: string
  county: string
  school_code: string
  phone: string
  email: string
  logo_url: string | null
  is_active: boolean
  student_count: number
  counselor_count: number
}

export interface SchoolDetail extends SchoolItem {
  counselors: {
    id: number
    first_name: string
    last_name: string
    email: string
    student_count: number
  }[]
  recent_students: {
    id: number
    first_name: string
    last_name: string
    grade: number
    created_at: string
  }[]
}

export interface PaginatedResponse<T> {
  results: T[]
  total: number
  page: number
  page_size: number
}

export interface UserItem {
  id: number
  first_name: string
  last_name: string
  email: string
  role: string
  county: string | null
  school_name: string | null
  is_active: boolean
  is_email_verified: boolean
  created_at: string
}

export interface UserDetail extends UserItem {
  school_id: number | null
  last_login: string | null
  grade?: number | null
  mode?: string | null
  has_assessment?: boolean
  student_count?: number
}

export interface AuditEntry {
  id: number
  actor_email: string | null
  actor_name: string | null
  action: string
  target_type: string
  target_id: number
  details: Record<string, unknown>
  ip_address: string | null
  created_at: string
}

export const systemAdminApi = {
  getDashboard: () =>
    api.get<{ data: DashboardData }>('/system-admin/dashboard/'),

  getSchools: (params?: { county?: string; search?: string; active?: string; page?: number }) =>
    api.get<{ data: PaginatedResponse<SchoolItem> }>('/system-admin/schools/', { params }),

  createSchool: (data: { name: string; county: string; school_code: string; phone?: string; email?: string }) =>
    api.post<{ data: SchoolItem }>('/system-admin/schools/', data),

  getSchool: (id: number) =>
    api.get<{ data: SchoolDetail }>(`/system-admin/schools/${id}/`),

  updateSchool: (id: number, data: { name?: string; phone?: string; email?: string }) =>
    api.patch<{ data: SchoolItem }>(`/system-admin/schools/${id}/`, data),

  deactivateSchool: (id: number) =>
    api.post(`/system-admin/schools/${id}/deactivate/`),

  activateSchool: (id: number) =>
    api.post(`/system-admin/schools/${id}/activate/`),

  getUsers: (params?: { role?: string; county?: string; school?: string; search?: string; active?: string; page?: number }) =>
    api.get<{ data: PaginatedResponse<UserItem> }>('/system-admin/users/', { params }),

  getUser: (id: number) =>
    api.get<{ data: UserDetail }>(`/system-admin/users/${id}/`),

  deactivateUser: (id: number) =>
    api.post(`/system-admin/users/${id}/deactivate/`),

  activateUser: (id: number) =>
    api.post(`/system-admin/users/${id}/activate/`),

  getAuditLogs: (params?: { action?: string; actor?: string; date_from?: string; date_to?: string; page?: number }) =>
    api.get<{ data: PaginatedResponse<AuditEntry> }>('/system-admin/audit-logs/', { params }),
}
