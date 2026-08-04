import api from '../lib/axios'

export const reportsApi = {
  downloadStudentPdf: (studentId: number) =>
    api.get(`/reports/student/${studentId}/pdf/`, { responseType: 'blob' }),
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
