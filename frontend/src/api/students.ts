import api from '../lib/axios'
import type { CounselorIntervention } from './counselor'
import type { AssessmentResult } from './assessment'
import type { CounselorInfo } from './dashboard'
import type { LearnerCombinationChoice } from './guidance'
import type { Notification } from './notifications'

export type AcademicGrade = 9 | 10 | 11 | 12

export interface StudentProfile {
  id: number
  email: string
  first_name: string
  last_name: string
  county: string | null
  grade: AcademicGrade
  mode: 'self_guided' | 'school_linked'
  school_membership_status: 'not_applicable' | 'pending' | 'active' | 'rejected'
  bio: string
  date_of_birth: string | null
  career_interests: string
  photo_url: string | null
}

export interface Subject {
  id: number
  name: string
  code: string
  continuity_code: string
  grade: AcademicGrade
  category: 'Core' | 'Elective' | 'Optional' | 'Required'
  is_selectable_in_combination?: boolean
  is_active: boolean
}

export interface StudentSubject {
  id: number
  subject: Subject
  continuity_code: string
  academic_grade: AcademicGrade
  academic_year: number
  is_active: boolean
  ended_at: string | null
  created_at: string
}

export type GradeLevel = 'EE1' | 'EE2' | 'ME1' | 'ME2' | 'AE1' | 'AE2' | 'BE1' | 'BE2'

export const GRADE_LEVEL_ORDER: GradeLevel[] = [
  'EE1', 'EE2', 'ME1', 'ME2', 'AE1', 'AE2', 'BE1', 'BE2',
]

export const GRADE_LEVEL_POINTS: Record<GradeLevel, number> = {
  EE1: 8,
  EE2: 7,
  ME1: 6,
  ME2: 5,
  AE1: 4,
  AE2: 3,
  BE1: 2,
  BE2: 1,
}

export const GRADE_LEVEL_LABELS: Record<GradeLevel, string> = {
  EE1: 'Exceeding Expectation - Level 1',
  EE2: 'Exceeding Expectation - Level 2',
  ME1: 'Meeting Expectation - Level 1',
  ME2: 'Meeting Expectation - Level 2',
  AE1: 'Approaching Expectation - Level 1',
  AE2: 'Approaching Expectation - Level 2',
  BE1: 'Below Expectation - Level 1',
  BE2: 'Below Expectation - Level 2',
}

export interface CBCGrade {
  id: number
  term: 1 | 2 | 3
  year: number
  level: GradeLevel
  source: 'learner' | 'school'
  verified_by: number | null
  verified_at: string | null
  created_at: string
  updated_at: string
}

export type ProgressStatus =
  | 'support'
  | 'insufficient_evidence'
  | 'needs_attention'
  | 'strong'
  | 'on_track'

export type ProgressRuleCode =
  | 'missing_evidence'
  | 'latest_be_support'
  | 'one_non_be_insufficient'
  | 'two_ae_be_support'
  | 'latest_ae_or_two_declines_attention'
  | 'latest_ee_or_improving_to_me2_strong'
  | 'otherwise_me_on_track'

export interface ProgressEvidence {
  id: number
  academic_grade: AcademicGrade
  year: number
  term: 1 | 2 | 3
  level: GradeLevel
  rank: number
  framework: { code: string; version: string }
  source: 'learner' | 'school'
  verified_by: number | null
  verified_school: number | null
  verified_at: string | null
  created_at: string
}

export interface SubjectProgress {
  continuity_code: string
  subject_name: string
  status: ProgressStatus
  label: string
  rule_code: ProgressRuleCode
  explanation: string
  suggested_action: string
  evidence_confidence: 'school_verified' | 'learner_entered' | 'mixed'
  records_used: ProgressEvidence[]
  evidence: ProgressEvidence[]
}

export interface ProgressAssessment {
  subjects: SubjectProgress[]
  overall: {
    status: ProgressStatus
    label: string
    subject_continuity_codes: string[]
  }
  advisory_disclaimer: string
}

export interface EvidenceSummary {
  profile_completion: {
    status: 'complete' | 'incomplete'
    percent: number
    missing_fields: string[]
  }
  academic_evidence: {
    status: 'not_started' | 'in_progress' | 'ready'
    total_subjects: number
    subjects_with_evidence: number
    total_grade_records: number
  }
  assessment: {
    status: 'not_started' | 'complete'
    instrument_version: string | null
    submitted_at: string | null
  }
  saved_combination_count: number
  plan_status: string
  next_action: {
    code: string
    title: string
    href: string
  }
}

export interface StudentGradeSummary {
  status: 'not_started' | 'in_progress' | 'ready'
  total_subjects: number
  subjects_with_evidence: number
  total_grade_records: number
  subjects: Array<{
    enrollment_id: number
    subject: Subject
    grades: CBCGrade[]
    latest_grade: CBCGrade | null
  }>
}

export interface StudentDashboardPayload {
  profile: StudentProfile
  grade_summary: StudentGradeSummary
  evidence: EvidenceSummary
  choices: LearnerCombinationChoice[]
  assessment: AssessmentResult | null
  counselor: CounselorInfo | null
  notifications: Notification[]
  interventions: CounselorIntervention[]
}

export type ParentAccessStatus =
  | 'invited'
  | 'pending_learner'
  | 'active'
  | 'revoked'

export interface ParentAccess {
  id: number
  parent_name: string
  parent_email: string
  claimed_relationship: 'mother' | 'father' | 'guardian' | 'relative' | 'other'
  relationship_label: string
  status: ParentAccessStatus
  learner_approved_at: string | null
  revoked_at: string | null
  created_at: string
}

export const studentsApi = {
  getDashboard: () =>
    api.get<{ data: StudentDashboardPayload }>('/students/dashboard/'),

  getEvidenceSummary: () =>
    api.get<{ data: EvidenceSummary }>('/students/evidence-summary/'),

  getProgress: () =>
    api.get<{ data: ProgressAssessment }>('/students/progress/'),

  getInterventions: () =>
    api.get<{ data: CounselorIntervention[] }>('/students/interventions/'),

  getParentAccess: () =>
    api.get<{ data: ParentAccess[] }>('/students/parent-access/'),

  approveParentAccess: (linkId: number) =>
    api.put<{ data: ParentAccess }>(
      `/students/parent-access/${linkId}/approve/`,
      {},
    ),

  revokeParentAccess: (linkId: number) =>
    api.put<{ data: ParentAccess }>(
      `/students/parent-access/${linkId}/revoke/`,
      {},
    ),

  getProfile: () =>
    api.get<{ data: StudentProfile }>('/students/profile/'),

  updateProfile: (data: Partial<Pick<StudentProfile, 'bio' | 'date_of_birth' | 'career_interests'>>) =>
    api.patch<{ data: StudentProfile }>('/students/profile/', data),

  uploadPhoto: (file: File) => {
    const form = new FormData()
    form.append('photo', file)
    return api.post<{ data: { photo_url: string } }>('/students/profile/photo/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  removePhoto: () => api.delete('/students/profile/photo/'),

  getSubjects: (grade: AcademicGrade) =>
    api.get<{ data: Subject[] }>(`/students/subjects/?grade=${grade}`),

  getMySubjects: () =>
    api.get<{ data: StudentSubject[] }>('/students/my-subjects/'),

  enrollSubject: (subjectId: number) =>
    api.post<{ data: StudentSubject }>('/students/my-subjects/', { subject_id: subjectId }),

  removeSubject: (id: number) =>
    api.post(`/students/my-subjects/${id}/remove/`, { confirm: true }),

  getGrades: (studentSubjectId: number) =>
    api.get<{ data: CBCGrade[] }>(`/students/my-subjects/${studentSubjectId}/grades/`),

  addGrade: (studentSubjectId: number, data: { term: number; year: number; level: GradeLevel }) =>
    api.post<{ data: CBCGrade }>(`/students/my-subjects/${studentSubjectId}/grades/`, data),

  updateGrade: (
    studentSubjectId: number,
    gradeId: number,
    data: { term: number; year: number; level: GradeLevel },
  ) =>
    api.put<{ data: CBCGrade }>(
      `/students/my-subjects/${studentSubjectId}/grades/${gradeId}/`,
      data,
    ),

  deleteGrade: (studentSubjectId: number, gradeId: number) =>
    api.delete(`/students/my-subjects/${studentSubjectId}/grades/${gradeId}/`),
}
