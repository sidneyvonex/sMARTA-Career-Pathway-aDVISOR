import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { DashboardAction } from './types'

interface Props {
  title: string
  description: string
  action?: DashboardAction
  icon?: ReactNode
}

export default function EmptyState({ title, description, action, icon }: Props) {
  return (
    <section className="db-state db-state--empty" aria-label={title}>
      {icon && <div className="db-state__icon" aria-hidden="true">{icon}</div>}
      <h3>{title}</h3>
      <p>{description}</p>
      {action?.to && <Link to={action.to} className="db-state__action">{action.label}</Link>}
      {action && !action.to && (
        <button type="button" className="db-state__action" onClick={action.onClick}>{action.label}</button>
      )}
    </section>
  )
}
