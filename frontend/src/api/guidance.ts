import api from '../lib/axios'


export interface GuidanceFramework {
  id: number
  code: string
  title: string
  description: string
  source_url: string
  effective_date: string
  is_active: boolean
}

export type GuidanceFrameworkSummary = Pick<
  GuidanceFramework,
  'code' | 'title' | 'source_url' | 'effective_date'
>

export interface GuidancePathwaySummary {
  id: number
  name: string
  description: string
}

export interface GuidanceTrack {
  id: number
  code: string
  name: string
  description: string
  is_active: boolean
  pathway: GuidancePathwaySummary
}

export interface GuidancePathway extends GuidancePathwaySummary {
  tracks: GuidanceTrack[]
}

export interface GuidanceSubject {
  id: number
  code: string
  name: string
  grade: 10
  category: 'Elective'
}

export interface GuidanceSchool {
  id: number
  school_code: string
  name: string
  county: string
}

export interface GuidanceCombination {
  id: number
  code: string
  title: string
  description: string
  related_routes: string[]
  framework: GuidanceFrameworkSummary
  track: GuidanceTrack
  subjects: [GuidanceSubject, GuidanceSubject, GuidanceSubject]
  offered_schools: GuidanceSchool[]
}

export interface SchoolOfferings {
  school: GuidanceSchool
  combination_ids: number[]
  offerings: GuidanceCombination[]
}

export interface LearnerCombinationChoice {
  id: number
  combination: GuidanceCombination
  status: 'saved' | 'provisional'
  learner_reason: string
  created_at: string
  updated_at: string
}

export interface GuidanceCombinationFilters {
  pathway?: string | number
  track?: string | number
  county?: string
  school?: string | number
  search?: string
}

interface ApiEnvelope<T> {
  data: T
  error: null
  message: string
}

const rootKey = ['guidance'] as const

export const guidanceKeys = {
  all: rootKey,
  framework: () => [...rootKey, 'framework', 'current'] as const,
  pathways: () => [...rootKey, 'pathways'] as const,
  combinations: (filters: GuidanceCombinationFilters = {}) =>
    [...rootKey, 'combinations', filters] as const,
  combination: (combinationId: number) =>
    [...rootKey, 'combinations', 'detail', combinationId] as const,
  schoolOfferings: () => [...rootKey, 'school-offerings'] as const,
  learnerChoices: () => [...rootKey, 'learner-choices'] as const,
}

export const guidanceApi = {
  getFramework: () =>
    api.get<ApiEnvelope<GuidanceFramework>>('/guidance/framework/current/'),

  getPathways: () =>
    api.get<ApiEnvelope<GuidancePathway[]>>('/guidance/pathways/'),

  getCombinations: (params: GuidanceCombinationFilters = {}) =>
    api.get<ApiEnvelope<GuidanceCombination[]>>('/guidance/combinations/', {
      params,
    }),

  getCombination: (combinationId: number) =>
    api.get<ApiEnvelope<GuidanceCombination>>(
      `/guidance/combinations/${combinationId}/`,
    ),

  getSchoolOfferings: () =>
    api.get<ApiEnvelope<SchoolOfferings>>('/school-admin/offerings/'),

  replaceSchoolOfferings: (combinationIds: number[]) =>
    api.put<ApiEnvelope<SchoolOfferings>>('/school-admin/offerings/', {
      combination_ids: combinationIds,
    }),

  getLearnerChoices: () =>
    api.get<ApiEnvelope<LearnerCombinationChoice[]>>(
      '/students/combination-choices/',
    ),

  saveLearnerChoice: (combinationId: number, learnerReason = '') =>
    api.post<ApiEnvelope<LearnerCombinationChoice>>(
      '/students/combination-choices/',
      {
        combination_id: combinationId,
        learner_reason: learnerReason,
      },
    ),

  removeLearnerChoice: (choiceId: number) =>
    api.delete<ApiEnvelope<null>>(`/students/combination-choices/${choiceId}/`),

  setProvisionalChoice: (choiceId: number) =>
    api.put<ApiEnvelope<LearnerCombinationChoice>>(
      `/students/combination-choices/${choiceId}/provisional/`,
      {},
    ),
}
