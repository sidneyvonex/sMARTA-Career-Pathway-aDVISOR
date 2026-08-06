import api from '../lib/axios'

export interface StudentReportFilters {
  year?: number
  term?: 1 | 2 | 3
  subject?: string
  academic?: boolean
}

export const reportsApi = {
  downloadStudentPdf: (studentId: number, filters?: StudentReportFilters) =>
    api.get(`/reports/student/${studentId}/pdf/`, {
      responseType: 'blob',
      params: filters,
    }),
  downloadSchoolOverviewPdf: () =>
    api.get('/reports/school/overview/pdf/', { responseType: 'blob' }),
  downloadSchoolRosterPdf: (grade?: number) =>
    api.get('/reports/school/roster/pdf/', {
      responseType: 'blob',
      params: grade ? { grade } : undefined,
    }),
  downloadCounselorOverviewPdf: () =>
    api.get('/reports/counselor/overview/pdf/', { responseType: 'blob' }),
  downloadCounselorRosterPdf: (grade?: number) =>
    api.get('/reports/counselor/roster/pdf/', {
      responseType: 'blob',
      params: grade ? { grade } : undefined,
    }),
  downloadPlatformOverviewPdf: () =>
    api.get('/reports/system/overview/pdf/', { responseType: 'blob' }),
  downloadSchoolsDirectoryPdf: () =>
    api.get('/reports/system/schools/pdf/', { responseType: 'blob' }),
}
