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
  grade: 9 | 10
  county: string | null
  photo_url: string | null
  top_pathway: string | null
  fit_pct: number | null
  quiz_status: 'done' | 'pending'
  last_active: string | null
}

export interface CounselorStats {
  total_students: number
  assessments_done: number
  students_needing_attention: number
  notes_written: number
}

export interface LinkedChild {
  id: number
  first_name: string
  last_name: string
  grade: 9 | 10
  county: string | null
  photo_url: string | null
  quiz_status: 'done' | 'pending'
  subject_count: number
  counselor_assigned: boolean
  last_active: string | null
  top_pathway: string | null
  fit_pct: number | null
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
