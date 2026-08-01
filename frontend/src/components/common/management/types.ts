import type { ReactNode } from 'react'

export interface ManagementAction {
  id: string
  label: string
  /**
   * Optional compact text for the row's primary action button. When set, the
   * button shows this (e.g. "View") while `label` remains the accessible name,
   * so long record names never overflow the action column.
   */
  shortLabel?: string
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
