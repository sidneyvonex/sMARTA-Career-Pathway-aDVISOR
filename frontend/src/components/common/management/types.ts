import type { ReactNode } from 'react'

export interface ManagementAction {
  id: string
  label: string
  onSelect: () => void
  tone?: 'default' | 'danger'
  disabled?: boolean
}

export interface ManagementColumn<T> {
  key: string
  label: string
  render: (record: T) => ReactNode
  priority?: 'identity' | 'essential' | 'secondary' | 'action'
  align?: 'start' | 'center' | 'end'
}

export interface PaginationState {
  page: number
  pageSize: 10 | 25 | 50
  total: number
}
