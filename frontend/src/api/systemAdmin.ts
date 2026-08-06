import api from '../lib/axios'

export interface DashboardData {
  users_by_role: Record<string, number>
  schools_by_county: Record<string, number>
  total_schools: number
  registered_learners: number
  learners_by_county: Record<string, number>
  verified_learners: number
  pending_school_links: number
  assignment_coverage: {
    assigned: number
    eligible: number
    percent: number
  }
  plans_completed: number
  framework: {
    code: string
    title: string
    source_url: string
    effective_date: string
  } | null
  recent_signups: number
  recent_audit: AuditEntry[]
}

export interface SchoolItem {
  id: number
  name: string
  county: string
  school_code: string | null
  phone: string
  email: string
  logo_url: string | null
  is_active: boolean
  verification_status: 'unverified' | 'verified' | 'demonstration'
  source_url: string
  source_checked_at: string | null
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

export interface CatalogueCombination {
  id: number
  code: string
  title: string
  description: string
  related_routes: string[]
  is_active: boolean
  track: {
    id: number
    code: string
    name: string
    is_active: boolean
    pathway: {
      id: number
      name: string
    }
  }
  subjects: {
    id: number
    code: string
    name: string
  }[]
  active_school_count: number
  learner_choice_count: number
}

export interface CatalogueData {
  framework: {
    id: number
    code: string
    title: string
    description: string
    source_url: string
    effective_date: string
    is_active: boolean
  } | null
  combinations: CatalogueCombination[]
}

export interface AssessmentFrameworkMetadata {
  id: number
  record_type: 'assessment_framework'
  code: string
  version: string
  title: string
  scope: string
  source_url: string
  effective_date: string
  status: 'draft' | 'active' | 'retired'
  level_count: number
  evidence_count: number
  can_change_status: boolean
}

export interface TertiarySourceMetadata {
  id: number
  record_type: 'institution' | 'programme'
  name: string
  source_scope: string
  external_key: string
  source_url: string
  education_framework: string
  admission_cycle: string
  effective_date: string
  verification_status: 'verified' | 'historical' | 'unavailable'
  can_change_status: boolean
}

export interface AcademicSourceMetadataData {
  assessment_frameworks: AssessmentFrameworkMetadata[]
  tertiary_sources: TertiarySourceMetadata[]
}

export const systemAdminApi = {
  getDashboard: () =>
    api.get<{ data: DashboardData }>('/system-admin/dashboard/'),

  getCatalogue: () =>
    api.get<{ data: CatalogueData }>('/system-admin/catalogue/'),

  updateCombinationStatus: (id: number, isActive: boolean) =>
    api.patch<{ data: CatalogueCombination }>(
      `/system-admin/catalogue/combinations/${id}/`,
      { is_active: isActive },
    ),

  getAcademicSourceMetadata: () =>
    api.get<{ data: AcademicSourceMetadataData }>('/system-admin/source-metadata/'),

  updateSourceStatus: (
    recordType: AssessmentFrameworkMetadata['record_type'] | TertiarySourceMetadata['record_type'],
    id: number,
    status: string,
  ) => api.patch(
    `/system-admin/source-metadata/${recordType}/${id}/`,
    { status },
  ),

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

  transferSchoolAdmin: (schoolId: number, newAdminUserId: number) =>
    api.post<{ message: string }>(`/system-admin/schools/${schoolId}/transfer-admin/`, {
      new_admin_user_id: newAdminUserId,
    }),

  getUsers: (params?: { role?: string; county?: string; school?: string; search?: string; active?: string; page?: number }) =>
    api.get<{ data: PaginatedResponse<UserItem> }>('/system-admin/users/', { params }),

  getUser: (id: number) =>
    api.get<{ data: UserDetail }>(`/system-admin/users/${id}/`),

  deactivateUser: (id: number) =>
    api.post(`/system-admin/users/${id}/deactivate/`),

  activateUser: (id: number) =>
    api.post(`/system-admin/users/${id}/activate/`),

  resetUserPassword: (id: number) =>
    api.post<{ message: string }>(`/system-admin/users/${id}/reset-password/`),

  getAuditLogs: (params?: { action?: string; actor?: string; date_from?: string; date_to?: string; page?: number }) =>
    api.get<{ data: PaginatedResponse<AuditEntry> }>('/system-admin/audit-logs/', { params }),
}
