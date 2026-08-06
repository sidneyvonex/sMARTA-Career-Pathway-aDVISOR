import api from '../lib/axios'

export interface LetterSummary {
  id: number
  to_email: string
  subject: string
  created_at: string
}

export interface LetterDetail extends LetterSummary {
  from_email: string
  body: string
}

type Envelope<T> = { data: T; error: null; message: string }

export const devMailApi = {
  list: () => api.get<Envelope<LetterSummary[]>>('/dev/letters/'),
  get: (id: number) => api.get<Envelope<LetterDetail>>(`/dev/letters/${id}/`),
  clear: () => api.delete<Envelope<{ deleted: number }>>('/dev/letters/'),
}
