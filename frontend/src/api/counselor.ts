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
}

export interface CounselorNote {
  id: number
  student: number
  student_name: string
  body: string
  created_at: string
  updated_at: string
}

export const counselorApi = {
  getStudents: () =>
    api.get<{ data: AssignedStudent[] }>('/counselors/students/'),

  getStudent: (studentId: number) =>
    api.get<{ data: StudentDetail }>(`/counselors/students/${studentId}/`),

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
}
