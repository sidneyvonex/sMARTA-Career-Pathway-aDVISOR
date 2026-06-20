import api from '../lib/axios'

export const reportsApi = {
  downloadStudentPdf: (studentId: number) =>
    api.get(`/reports/student/${studentId}/pdf/`, { responseType: 'blob' }),
}
