import api from '../lib/axios'

export interface CounselorInfo {
  id: number
  first_name: string
  last_name: string
  email: string
  county: string | null
  photo_url: string | null
  last_message: string | null
  last_message_at: string | null
}

export interface AssignedStudent {
  id: number
  first_name: string
  last_name: string
  grade: 9 | 10 | 11 | 12
  county: string | null
  photo_url: string | null
  top_pathway: string | null
  quiz_status: 'done' | 'pending'
  needs_attention: boolean
  attention_reasons: {
    code:
      | 'assessment_missing'
      | 'academic_evidence_missing'
      | 'no_saved_combination'
      | 'no_plan'
      | 'learner_requested_review'
      | 'follow_up_overdue'
      | 'combination_unavailable_at_school'
    label: string
    guidance: string
  }[]
  last_active: string | null
}

export interface CounselorStats {
  total_students: number
  assessments_done: number
  students_needing_attention: number
  follow_ups_due: number
  journeys_reviewed: number
  notes_written: number
}

export interface LinkedChild {
  id: number
  first_name: string
  last_name: string
  grade: 9 | 10 | 11 | 12
  county: string | null
  photo_url: string | null
  quiz_status: 'done' | 'pending'
  subject_count: number
  counselor_assigned: boolean
  last_active: string | null
  top_pathway: string | null
  access_status: 'active'
  next_action: {
    code: string
    title: string
  }
  provisional_combination: {
    id: number
    code: string
    title: string
    pathway: string
    track: string
  } | null
  plan_status: 'not_started' | 'draft' | 'ready_for_review' | 'reviewed'
  plan_progress: {
    completed: number
    total: number
  }
  upcoming_milestone: {
    id: number
    title: string
    due_date: string | null
  } | null
  conversation_prompt: string
}

export const dashboardApi = {
  getStudentCounselor: () =>
    api.get<{ data: CounselorInfo | null }>('/students/counselor/'),

  getCounselorStudents: () =>
    api.get<{ data: AssignedStudent[] }>('/counselors/students/'),

  getCounselorStats: () =>
    api.get<{ data: CounselorStats }>('/counselors/stats/'),

  getParentChildren: () =>
    api.get<{ data: LinkedChild[] }>('/parents/children/'),
}
