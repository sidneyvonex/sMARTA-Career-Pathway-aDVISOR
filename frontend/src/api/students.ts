import api from '../lib/axios'
import type { CounselorIntervention } from './counselor'
import type { AssessmentResult } from './assessment'
import type { CounselorInfo } from './dashboard'
import type { LearnerCombinationChoice } from './guidance'
import type { Notification } from './notifications'

export type AcademicGrade = 9 | 10 | 11 | 12

export type JourneyStatus =
  | ''
  | 'not_selected'
  | 'selected'
  | 'currently_enrolled'
  | 'reconsidering'
  | 'unsure'

export type SelectionSource =
  | ''
  | 'smarta_shauri'
  | 'learner_reported'
  | 'school_verified'
  | 'ministry_imported'

/** Journey stages where the learner already has a pathway on record and RIASEC
 * is optional rather than a prerequisite. */
export const SELECTED_JOURNEY_STAGES: JourneyStatus[] = [
  'selected',
  'currently_enrolled',
]

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
  journey_status: JourneyStatus
  current_pathway: number | null
  current_pathway_name: string | null
  current_subject_combination: string
  selection_source: SelectionSource
  selection_date: string | null
  selection_verified: boolean
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
  academic_grade?: AcademicGrade
  term: 1 | 2 | 3
  year: number
  level: GradeLevel
  source: 'learner' | 'school'
  verified_by: number | null
  verified_school?: number | null
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
  decision_inputs: {
    latest_framework: { code: string; version: string } | null
    me2_rank: number | null
  }
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

export type AcademicGoalStatus = 'active' | 'achieved' | 'closed'

export interface AcademicGoalLevelSnapshot {
  id?: number
  code: GradeLevel
  rank: number
  framework: { code: string; version: string }
}

export interface AcademicGoalEvidenceSnapshot {
  evidence_id: number
  period: {
    academic_grade: AcademicGrade
    year: number
    term: 1 | 2 | 3
  }
  level: { code: GradeLevel; rank: number }
  framework: {
    id: number
    code: string
    version: string
    level_ranks: Partial<Record<GradeLevel, number>>
  }
  source: 'learner' | 'school'
  verification: {
    confidence: 'learner_entered' | 'school_verified'
    verified_by: number | null
    verified_school: number | null
    verified_at: string | null
  }
  recorded_at: string
  snapshot_provenance?: 'migration_0013_best_available'
}

export interface AcademicGoal {
  id: number
  continuity_code: string
  current_evidence: number | null
  creation_evidence_snapshot: AcademicGoalEvidenceSnapshot
  current_level: AcademicGoalLevelSnapshot
  target_level: AcademicGoalLevelSnapshot & { id: number }
  target_term: 1 | 2 | 3
  target_year: number
  target_academic_grade: AcademicGrade
  action_plan: string
  status: AcademicGoalStatus
  ready_for_achievement: boolean
  readiness_evidence: number | null
  achievement_evidence_snapshot: AcademicGoalEvidenceSnapshot | null
  legacy_lifecycle_unverifiable: boolean
  created_by: number
  confirmed_by: number | null
  achieved_at: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
}

export interface AcademicGoalCreate {
  continuity_code: string
  target_level: GradeLevel
  target_term: 1 | 2 | 3
  target_year: number
  target_academic_grade: AcademicGrade
  action_plan: string
}

export type AcademicGoalUpdate = Partial<Pick<
  AcademicGoalCreate,
  'target_level' | 'target_term' | 'target_year' |
  'target_academic_grade' | 'action_plan'
>>

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
  journey: JourneySummary
  saved_combination_count: number
  plan_status: string
  next_action: {
    code: string
    title: string
    href: string
  }
}

export interface JourneySummary {
  status: JourneyStatus
  current_pathway: { id: number; name: string } | null
  current_subject_combination: string
  selection_source: SelectionSource
  selection_date: string | null
  selection_verified: boolean
}

/** True when the learner already has a pathway on record, so RIASEC is an
 * optional career-reflection tool rather than a required step. */
export function hasSelectedPathway(status: JourneyStatus): boolean {
  return SELECTED_JOURNEY_STAGES.includes(status)
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

  getAcademicGoals: (studentId?: number) =>
    api.get<{ data: AcademicGoal[] }>(
      studentId === undefined
        ? '/students/academic-goals/'
        : `/students/academic-goals/?student_id=${studentId}`,
    ),

  getAcademicGoal: (goalId: number) =>
    api.get<{ data: AcademicGoal }>(`/students/academic-goals/${goalId}/`),

  createAcademicGoal: (data: AcademicGoalCreate) =>
    api.post<{ data: AcademicGoal; message: string }>(
      '/students/academic-goals/',
      data,
    ),

  updateAcademicGoal: (goalId: number, data: AcademicGoalUpdate) =>
    api.patch<{ data: AcademicGoal; message: string }>(
      `/students/academic-goals/${goalId}/`,
      data,
    ),

  closeAcademicGoal: (goalId: number) =>
    api.delete<{ data: AcademicGoal; message: string }>(
      `/students/academic-goals/${goalId}/`,
    ),

  confirmAcademicGoalAchievement: (goalId: number) =>
    api.post<{ data: AcademicGoal; message: string }>(
      `/students/academic-goals/${goalId}/confirm-achievement/`,
      { confirm: true },
    ),

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

  updateProfile: (
    data: Partial<Pick<
      StudentProfile,
      | 'bio'
      | 'date_of_birth'
      | 'career_interests'
      | 'journey_status'
      | 'current_pathway'
      | 'current_subject_combination'
      | 'selection_source'
      | 'selection_date'
    >>,
  ) =>
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
