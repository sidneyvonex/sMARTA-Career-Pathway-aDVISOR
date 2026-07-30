import api from '../lib/axios'

export interface StudentProfile {
  id: number
  email: string
  first_name: string
  last_name: string
  county: string | null
  grade: 9 | 10
  mode: 'self_guided' | 'school_linked'
  bio: string
  date_of_birth: string | null
  career_interests: string
  photo_url: string | null
}

export interface Subject {
  id: number
  name: string
  code: string
  grade: 9 | 10
  category: 'Core' | 'Optional'
}

export interface StudentSubject {
  id: number
  subject: Subject
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
  created_at: string
  updated_at: string
}

export const studentsApi = {
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

  getSubjects: (grade: 9 | 10) =>
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
