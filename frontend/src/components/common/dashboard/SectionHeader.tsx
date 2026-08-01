import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { DashboardAction } from './types'

interface Props {
  title: string
  eyebrow?: string
  description?: ReactNode
  action?: DashboardAction
  aside?: ReactNode
  className?: string
  titleAs?: 'h1' | 'h2' | 'h3'
  titleId?: string
}

export default function SectionHeader({
  title,
  eyebrow,
  description,
  action,
  aside,
  className = '',
  titleAs = 'h2',
  titleId,
}: Props) {
  const Heading = titleAs
  const actionClass = 'db-section-header__action'

  return (
    <div className={`db-section-header ${className}`.trim()}>
      <div>
        {eyebrow && <span className="db-section-header__eyebrow">{eyebrow}</span>}
        <Heading className="db-section-header__title" id={titleId}>{title}</Heading>
        {description && <div className="db-section-header__description">{description}</div>}
      </div>
      {action?.to && <Link to={action.to} className={actionClass}>{action.label}</Link>}
      {action && !action.to && (
        <button type="button" className={actionClass} onClick={action.onClick}>{action.label}</button>
      )}
      {!action && aside}
    </div>
  )
}
