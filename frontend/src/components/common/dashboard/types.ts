import type { ReactNode } from 'react'

export type DashboardTone = 'student' | 'parent' | 'counsellor' | 'school' | 'system'
export type SurfaceTone = 'neutral' | 'positive' | 'warning' | 'attention' | 'info'

export interface DashboardAction {
  label: string
  to?: string
  onClick?: () => void
  variant?: 'primary' | 'secondary'
  icon?: ReactNode
}
