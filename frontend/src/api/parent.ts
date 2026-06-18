import api from '../lib/axios'

export interface ChildProfile {
  id: number
  first_name: string
  last_name: string
  email: string
  county: string | null
  grade: 9 | 10
  mode: 'self_guided' | 'school_linked'
  bio: string
  date_of_birth: string | null
  career_interests: string
  photo_url: string | null
}

export interface ChildGrade {
  id: number
  term: 1 | 2 | 3
  year: number
  level: string
}

export interface ChildSubject {
  id: number
  name: string
  code: string
  category: string
  grades: ChildGrade[]
}

export interface ChildRecommendation {
  rank: number
  fit_score: number
  fit_pct: number
  pathway: { id: number; name: string; description: string }
}

export interface ChildAssessment {
  id: number
  submitted_at: string
  holland_code: string
  scores: Record<string, number>
  recommendations: ChildRecommendation[]
}

export interface ChildCounselor {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface ChildNote {
  body: string
  created_at: string
  updated_at: string
}

export interface ChildDetail {
  profile: ChildProfile
  subjects: ChildSubject[]
  assessment: ChildAssessment | null
  counselor: ChildCounselor | null
  latest_note: ChildNote | null
}

export const parentApi = {
  getChildDetail: (studentId: number) =>
    api.get<{ data: ChildDetail }>(`/parents/children/${studentId}/`),
}
