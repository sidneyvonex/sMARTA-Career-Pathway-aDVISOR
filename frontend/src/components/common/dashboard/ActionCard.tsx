import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { SurfaceTone } from './types'

interface Props {
  title: string
  description: string
  to?: string
  onClick?: () => void
  icon?: ReactNode
  status?: ReactNode
  meta?: ReactNode
  tone?: SurfaceTone
}

export default function ActionCard({
  title,
  description,
  to,
  onClick,
  icon,
  status,
  meta,
  tone = 'neutral',
}: Props) {
  const className = `db-action-card db-action-card--${tone}`
  const content = (
    <>
      {icon && <span className="db-action-card__icon" aria-hidden="true">{icon}</span>}
      <span className="db-action-card__body">
        <span className="db-action-card__heading">
          <strong>{title}</strong>
          {status}
        </span>
        <span className="db-action-card__description">{description}</span>
        {meta && <span className="db-action-card__meta">{meta}</span>}
      </span>
      <span className="db-action-card__arrow" aria-hidden="true">→</span>
    </>
  )

  if (to) {
    return <Link to={to} className={className}>{content}</Link>
  }

  return <button type="button" className={className} onClick={onClick}>{content}</button>
}
