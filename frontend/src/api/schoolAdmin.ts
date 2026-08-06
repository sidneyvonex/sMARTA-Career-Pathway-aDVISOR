import api from '../lib/axios'
import type { AcademicPeriod, GradeLevel } from './students'

export interface SchoolProfile {
  id: number
  name: string
  county: string
  school_code: string | null
  logo_url: string | null
  phone: string
  email: string
  student_count: number
  counselor_count: number
}

export interface SchoolCounselor {
  id: number
  first_name: string
  last_name: string
  email: string
  student_count: number
  joined_at: string
}

export interface SchoolStudent {
  id: number
  first_name: string
  last_name: string
  email: string
  grade: number
  photo_url: string | null
  quiz_status: 'done' | 'pending'
  school_membership_status: 'pending' | 'active' | 'rejected' | 'ended' | 'not_applicable'
  school: { id: number; name: string } | null
  counselor_id: number | null
  counselor_name: string | null
  membership: {
    id: number
    status: 'pending' | 'active'
    record_source: 'legacy_backfill' | 'learner_request' | 'admin_import'
    requested_at: string | null
    started_at: string | null
    ended_at: string | null
  } | null
  transfer: { previous_membership_count: number }
  academic_evidence: {
    id: number
    continuity_code: string
    subject_name: string
    academic_grade: number
    term: 1 | 2 | 3
    year: number
    level: string
    framework: { code: string; version: string }
    source: 'learner' | 'school'
    verified_school: { id: number; name: string } | null
    verified_at: string | null
    can_verify: boolean
    can_remove_verification: boolean
  }[]
}

export interface SchoolMembershipRequest {
  student_id: number
  first_name: string
  last_name: string
  email: string
  grade: number
  requested_at: string
}

export interface SchoolStats {
  total_students: number
  total_counselors: number
  assessed: number
  unassigned: number
  pending_memberships: number
  evidence_complete: number
  choices_saved: number
  plans_created: number
  reviews_completed: number
  offerings_count: number
  offerings_configured: boolean
  academic_progress: SchoolProgressAggregate[]
  counselor_workload: {
    counselor_id: number
    counselor_name: string
    student_count: number
  }[]
}

export interface SchoolProgressAggregate {
  year: number
  term: 1 | 2 | 3
  level: string
  continuity_code: string
  subject_name: string
  count: number
}

export interface StudentImportResult {
  created_count: number
  linked_count: number
  already_linked_count: number
  error_count: number
  created: {
    id: number
    first_name: string
    last_name: string
    email: string
    grade: number
    temporary_password: string
  }[]
  linked: {
    id: number
    first_name: string
    last_name: string
    email: string
    grade: number
  }[]
  already_linked: {
    id: number
    first_name: string
    last_name: string
    email: string
    grade: number
  }[]
  errors: { row: number; email: string; message: string }[]
}

export interface MarksImportRow {
  row: number
  student_email: string
  subject_code: string
  level: string
  raw_score?: string | null
  action: 'create' | 'replace_learner_entry' | 'error'
  errors: string[]
}

export interface MarksImportResult {
  period: AcademicPeriod
  row_count: number
  valid_count: number
  error_count: number
  created_count?: number
  replaced_count?: number
  rows: MarksImportRow[]
}

export interface MarksImportTemplateRow {
  student_email: string
  subject_code: string
  level: GradeLevel
  raw_score?: string
}

export const schoolAdminApi = {
  getSchool: () =>
    api.get<{ data: SchoolProfile }>('/school-admin/school/'),

  updateSchool: (data: { name?: string; phone?: string; email?: string }) =>
    api.patch<{ data: SchoolProfile }>('/school-admin/school/', data),

  uploadLogo: (file: File) => {
    const form = new FormData()
    form.append('logo', file)
    return api.post<{ data: { logo_url: string } }>('/school-admin/school/logo/', form)
  },

  removeLogo: () =>
    api.post('/school-admin/school/logo/remove/'),

  getCounselors: () =>
    api.get<{ data: SchoolCounselor[] }>('/school-admin/counselors/'),

  addCounselor: (email: string) =>
    api.post<{ data: { id: number; email: string }; message: string }>('/school-admin/counselors/add/', { email }),

  removeCounselor: (counselorId: number) =>
    api.post('/school-admin/counselors/' + counselorId + '/remove/'),

  resetCounselorPassword: (counselorId: number) =>
    api.post<{ message: string }>('/school-admin/counselors/' + counselorId + '/reset-password/'),

  getStudents: () =>
    api.get<{ data: SchoolStudent[] }>('/school-admin/students/'),

  importStudents: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ data: StudentImportResult; message: string }>(
      '/school-admin/students/import/',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  getAcademicPeriods: () =>
    api.get<{ data: AcademicPeriod[] }>('/school-admin/academic-periods/'),

  importMarks: (periodId: number, file: File, preview: boolean) => {
    const form = new FormData()
    form.append('period_id', String(periodId))
    form.append('preview', String(preview))
    form.append('file', file)
    return api.post<{ data: MarksImportResult; message: string }>(
      '/school-admin/marks/import/',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  getMembershipRequests: () =>
    api.get<{ data: SchoolMembershipRequest[] }>('/school-admin/membership-requests/'),

  decideMembershipRequest: (studentId: number, decision: 'approve' | 'reject') =>
    api.put<{
      data: {
        student_id: number
        school_membership_status: 'active' | 'rejected'
      }
      message: string
    }>(`/school-admin/membership-requests/${studentId}/decision/`, { decision }),

  setGradeVerification: (studentId: number, gradeId: number, verified: boolean) =>
    api.put(
      `/school-admin/students/${studentId}/grades/${gradeId}/verification/`,
      { verified },
    ),

  resetStudentPassword: (studentId: number) =>
    api.post<{ message: string }>(`/school-admin/students/${studentId}/reset-password/`),

  getStats: () =>
    api.get<{ data: SchoolStats }>('/school-admin/stats/'),

  assignStudent: (studentId: number, counselorId: number) =>
    api.post('/school-admin/assignments/', {
      student_id: studentId,
      counselor_id: counselorId,
    }),

  bulkAssignStudents: (studentIds: number[], counselorId: number) =>
    api.post<{
      data: {
        assigned_count: number
        counselor_id: number
        student_ids: number[]
      }
      message: string
    }>('/school-admin/assignments/bulk/', {
      student_ids: studentIds,
      counselor_id: counselorId,
    }),

  removeAssignment: (assignmentId: number) =>
    api.post('/school-admin/assignments/' + assignmentId + '/remove/'),
}
