import type { ReactNode } from 'react'
import type { SurfaceTone } from './types'

interface Props {
  children: ReactNode
  tone?: SurfaceTone
}

export default function StatusBadge({ children, tone = 'neutral' }: Props) {
  return <span className={`db-status db-status--${tone}`}>{children}</span>
}
