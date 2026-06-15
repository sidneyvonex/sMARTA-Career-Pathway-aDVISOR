import api from '../lib/axios'

export type RIASECDimension = 'R' | 'I' | 'A' | 'S' | 'E' | 'C'

export const DIMENSION_LABELS: Record<RIASECDimension, string> = {
  R: 'Realistic',
  I: 'Investigative',
  A: 'Artistic',
  S: 'Social',
  E: 'Enterprising',
  C: 'Conventional',
}

export const LIKERT_LABELS: Record<number, string> = {
  1: 'Not at all like me',
  2: 'A little like me',
  3: 'Somewhat like me',
  4: 'Mostly like me',
  5: 'Very much like me',
}

export interface RIASECQuestion {
  id: number
  dimension: RIASECDimension
  text: string
  order: number
}

export interface Pathway {
  id: number
  name: string
  description: string
}

export interface AssessmentRecommendation {
  rank: number
  fit_score: number
  fit_pct: number
  pathway: Pathway
}

export interface AssessmentResult {
  id: number
  submitted_at: string
  holland_code: string
  scores: Record<RIASECDimension, number>
  recommendations: AssessmentRecommendation[]
}

export interface ResponseItem {
  question_id: number
  score: number
}

export const assessmentApi = {
  getQuestions: () =>
    api.get<{ data: RIASECQuestion[] }>('/students/assessment/questions/'),

  submitAssessment: (responses: ResponseItem[]) =>
    api.post<{ data: AssessmentResult }>('/students/assessment/', { responses }),

  getHistory: () =>
    api.get<{ data: AssessmentResult[] }>('/students/assessment/'),

  getLatest: () =>
    api.get<{ data: AssessmentResult }>('/students/assessment/latest/'),
}
