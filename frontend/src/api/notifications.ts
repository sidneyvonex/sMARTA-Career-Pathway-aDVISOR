import api from '../lib/axios'

export type NotificationType =
  | 'assessment_submitted'
  | 'counselor_note'
  | 'parent_linked'
  | 'counselor_assigned'
  | 'child_assessment_complete'
  | 'school_membership_decided'
  | 'grade_verification_changed'
  | 'school_transfer_decided'
  | 'counselor_intervention'
  | 'academic_goal_achieved'

export interface Notification {
  id: number
  type: NotificationType
  message: string
  read: boolean
  created_at: string
}

export interface UnreadCount {
  count: number
}

export const notificationsApi = {
  getList: () =>
    api.get<{ data: Notification[]; error: null; message: string }>('/notifications/'),

  getUnreadCount: () =>
    api.get<{ data: UnreadCount; error: null; message: string }>('/notifications/unread-count/'),

  markRead: (id: number) =>
    api.patch<{ data: Notification; error: null; message: string }>(`/notifications/${id}/read/`),

  markAllRead: () =>
    api.post<{ data: null; error: null; message: string }>('/notifications/mark-all-read/'),
}
