import api from '../lib/axios'
import type { AssignedStudent, CounselorStats } from './dashboard'

export interface StudentDetail {
  student: {
    id: number
    email: string
    first_name: string
    last_name: string
    grade: 9 | 10
    county: string | null
    school: string | null
    photo_url: string | null
    bio: string
    career_interests: string
    created_at: string
  }
  riasec_result: {
    id: number
    submitted_at: string
    holland_code: string
    scores: Record<string, number>
    recommendations: {
      rank: number
      fit_score: number
      fit_pct: number
      pathway: { id: number; name: string; description: string }
    }[]
  } | null
  grades: {
    id: number
    subject_name: string
    subject_code: string
    term: 1 | 2 | 3
    year: number
    level: string
    created_at: string
    updated_at: string
  }[]
  notes_count: number
  attention_reasons: AssignedStudent['attention_reasons']
  evidence_summary: {
    academic: {
      status: 'not_started' | 'in_progress' | 'ready'
      total_subjects: number
      subjects_with_evidence: number
      total_grade_records: number
    }
    assessment: { status: 'not_started' | 'complete' }
  }
  combination_choices: {
    id: number
    status: 'saved' | 'provisional'
    learner_reason: string
    code: string
    title: string
    pathway: string
    track: string
    subjects: string[]
  }[]
  plan: {
    status: 'draft' | 'ready_for_review' | 'reviewed'
    learner_reason: string
    milestones: {
      id: number
      title: string
      due_date: string | null
      is_complete: boolean
    }[]
  } | null
  interventions: CounselorIntervention[]
}

export interface CounselorNote {
  id: number
  student: number
  student_name: string
  body: string
  created_at: string
  updated_at: string
}

export type InterventionCategory =
  | 'assessment'
  | 'academic_evidence'
  | 'combination'
  | 'plan'
  | 'follow_up'
  | 'other'

export interface CounselorIntervention {
  id: number
  student: number
  student_name: string
  category: InterventionCategory
  action_agreed: string
  follow_up_date: string | null
  status: 'open' | 'completed'
  learner_visible: boolean
  parent_visible: boolean
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface InterventionInput {
  category: InterventionCategory
  action_agreed: string
  follow_up_date?: string | null
  learner_visible?: boolean
  parent_visible?: boolean
}

export interface PlanReviewResult {
  id: number
  status: 'ready_for_review' | 'reviewed'
  reviewed_at: string | null
}

export const counselorApi = {
  getStudents: () =>
    api.get<{ data: AssignedStudent[] }>('/counselors/students/'),

  getStudent: (studentId: number) =>
    api.get<{ data: StudentDetail }>(`/counselors/students/${studentId}/`),

  reviewPlan: (studentId: number, reviewed: boolean) =>
    api.put<{ data: PlanReviewResult }>(
      `/counselors/students/${studentId}/plan-review/`,
      { reviewed },
    ),

  getStats: () =>
    api.get<{ data: CounselorStats }>('/counselors/stats/'),

  getNotes: () =>
    api.get<{ data: CounselorNote[] }>('/counselors/notes/'),

  createNote: (studentId: number, body: string) =>
    api.post<{ data: CounselorNote }>('/counselors/notes/', {
      student_id: studentId,
      body,
    }),

  updateNote: (noteId: number, body: string) =>
    api.patch<{ data: CounselorNote }>(`/counselors/notes/${noteId}/`, { body }),

  deleteNote: (noteId: number) =>
    api.delete(`/counselors/notes/${noteId}/`),

  getInterventions: () =>
    api.get<{ data: CounselorIntervention[] }>('/counselors/interventions/'),

  createIntervention: (studentId: number, input: InterventionInput) =>
    api.post<{ data: CounselorIntervention }>('/counselors/interventions/', {
      student_id: studentId,
      ...input,
    }),

  updateIntervention: (
    interventionId: number,
    input: Partial<InterventionInput & { status: 'open' | 'completed' }>,
  ) =>
    api.patch<{ data: CounselorIntervention }>(
      `/counselors/interventions/${interventionId}/`,
      input,
    ),
}
