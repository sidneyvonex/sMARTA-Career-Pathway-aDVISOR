import api from '../lib/axios'

export interface SchoolProfile {
  id: number
  name: string
  county: string
  school_code: string
  logo_url: string | null
  phone: string
  email: string
  student_count: number
  counselor_count: number
}

export interface SchoolCounselor {
  id: number
  first_name: string
  last_name: string
  email: string
  student_count: number
  joined_at: string
}

export interface SchoolStudent {
  id: number
  first_name: string
  last_name: string
  email: string
  grade: number
  photo_url: string | null
  quiz_status: 'done' | 'pending'
  counselor_id: number | null
  counselor_name: string | null
}

export interface SchoolStats {
  total_students: number
  total_counselors: number
  assessed: number
  unassigned: number
}

export const schoolAdminApi = {
  getSchool: () =>
    api.get<{ data: SchoolProfile }>('/school-admin/school/'),

  updateSchool: (data: { name?: string; phone?: string; email?: string }) =>
    api.patch<{ data: SchoolProfile }>('/school-admin/school/', data),

  uploadLogo: (file: File) => {
    const form = new FormData()
    form.append('logo', file)
    return api.post<{ data: { logo_url: string } }>('/school-admin/school/logo/', form)
  },

  removeLogo: () =>
    api.delete('/school-admin/school/logo/'),

  getCounselors: () =>
    api.get<{ data: SchoolCounselor[] }>('/school-admin/counselors/'),

  addCounselor: (email: string) =>
    api.post<{ data: { id: number; email: string } }>('/school-admin/counselors/add/', { email }),

  removeCounselor: (counselorId: number) =>
    api.post('/school-admin/counselors/' + counselorId + '/remove/'),

  getStudents: () =>
    api.get<{ data: SchoolStudent[] }>('/school-admin/students/'),

  getStats: () =>
    api.get<{ data: SchoolStats }>('/school-admin/stats/'),

  assignStudent: (studentId: number, counselorId: number) =>
    api.post('/school-admin/assignments/', {
      student_id: studentId,
      counselor_id: counselorId,
    }),

  removeAssignment: (assignmentId: number) =>
    api.post('/school-admin/assignments/' + assignmentId + '/remove/'),
}
