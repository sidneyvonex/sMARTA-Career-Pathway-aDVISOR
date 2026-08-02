import api from '../lib/axios'
import type { CounselorIntervention } from './counselor'
import type { AcademicGoal, ProgressAssessment } from './students'
import type { EducationGoal } from './tertiary'

export interface ChildProfile {
  id: number
  first_name: string
  last_name: string
  email: string
  county: string | null
  grade: 9 | 10 | 11 | 12
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

export interface ChildAcademicReadiness {
  status: 'not_started' | 'in_progress' | 'ready'
  total_subjects: number
  subjects_with_evidence: number
  total_grade_records: number
}

export interface ChildProvisionalCombination {
  id: number
  code: string
  title: string
  pathway: string
  track: string
  subjects: string[]
}

export interface ChildPlan {
  status: 'draft' | 'ready_for_review' | 'reviewed'
  learner_reason: string
  milestones: {
    id: number
    title: string
    due_date: string | null
    is_complete: boolean
    completed_at: string | null
  }[]
}

export interface ChildDetail {
  profile: ChildProfile
  subjects: ChildSubject[]
  assessment: ChildAssessment | null
  academic_readiness: ChildAcademicReadiness
  provisional_combination: ChildProvisionalCombination | null
  plan: ChildPlan | null
  counselor: ChildCounselor | null
  latest_note: ChildNote | null
  parent_visible_notes: ChildNote[]
  interventions: CounselorIntervention[]
  academic_progress?: ProgressAssessment
  academic_goals?: AcademicGoal[]
  education_goals?: EducationGoal[]
}

export const parentApi = {
  getChildDetail: (studentId: number) =>
    api.get<{ data: ChildDetail }>(`/parents/children/${studentId}/`),
}
