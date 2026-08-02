import api from '../lib/axios'


export type VerificationStatus = 'verified' | 'historical' | 'unavailable'

export interface CatalogueProvenance {
  source_scope: string
  external_key: string
  source_url: string
  education_framework: string
  admission_cycle: string
  effective_date: string
  verification_status: VerificationStatus
}

export interface Institution extends CatalogueProvenance {
  id: number
  name: string
  institution_type: 'university' | 'college' | 'tvet' | 'other'
  county: string
  website_url: string
}

export interface ProgrammeSubjectReference extends CatalogueProvenance {
  id: number
  subject_code: string
  subject_name: string
  mapping_kind: 'historical_requirement' | 'exploratory_alignment'
  notes: string
  advisory_label: string
}

export interface HistoricalAdmissionReference extends CatalogueProvenance {
  id: number
  requirement_summary: string
  reference_status: 'historical_reference'
  reference_only: true
}

export interface Programme extends CatalogueProvenance {
  id: number
  institution: Institution
  code: string
  name: string
  description: string
}

export interface ProgrammeDetail extends Programme {
  subject_references: ProgrammeSubjectReference[]
  historical_admission_references: HistoricalAdmissionReference[]
}

export type EducationGoalKind = 'primary' | 'alternative'

export interface EducationGoal {
  id: number
  institution: Institution
  programme: Programme | null
  kind: EducationGoalKind
  priority: 1 | 2
  created_by: number
  created_at: string
  updated_at: string
}

export interface EducationGoalWrite {
  institution: number
  programme?: number | null
  kind: EducationGoalKind
  priority: 1 | 2
}

export interface CatalogueFilters {
  search?: string
  framework?: string
  cycle?: string
  verification_status?: VerificationStatus
}

function queryString(filters: object) {
  const query = new URLSearchParams()
  Object.entries(filters as Record<string, string | number | undefined>).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value))
  })
  const encoded = query.toString()
  return encoded ? `?${encoded}` : ''
}

export const tertiaryApi = {
  getInstitutions: (filters: CatalogueFilters & { county?: string } = {}) =>
    api.get<{ data: Institution[] }>(`/tertiary/institutions/${queryString(filters)}`),

  getProgrammes: (
    filters: CatalogueFilters & { institution?: number } = {},
  ) => api.get<{ data: Programme[] }>(`/tertiary/programmes/${queryString(filters)}`),

  getProgramme: (programmeId: number) =>
    api.get<{ data: ProgrammeDetail }>(`/tertiary/programmes/${programmeId}/`),

  getEducationGoals: () =>
    api.get<{ data: EducationGoal[] }>('/students/education-goals/'),

  createEducationGoal: (data: EducationGoalWrite) =>
    api.post<{ data: EducationGoal; message: string }>('/students/education-goals/', data),

  updateEducationGoal: (goalId: number, data: Partial<EducationGoalWrite>) =>
    api.patch<{ data: EducationGoal; message: string }>(
      `/students/education-goals/${goalId}/`, data,
    ),

  deleteEducationGoal: (goalId: number) =>
    api.delete<{ data: null; message: string }>(`/students/education-goals/${goalId}/`),
}
