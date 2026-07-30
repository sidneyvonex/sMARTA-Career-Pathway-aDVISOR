import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { DashboardAction, DashboardTone } from './types'

interface Props {
  eyebrow: string
  title: string
  description?: string
  meta?: string[]
  actions?: DashboardAction[]
  tone?: DashboardTone
  avatar?: ReactNode
  visual?: ReactNode
  className?: string
}

function HeroAction({ action }: { action: DashboardAction }) {
  const className = `db-hero__action db-hero__action--${action.variant ?? 'primary'}`
  const content = (
    <>
      {action.icon}
      <span>{action.label}</span>
    </>
  )

  if (action.to) {
    return <Link to={action.to} className={className}>{content}</Link>
  }

  return (
    <button type="button" className={className} onClick={action.onClick}>
      {content}
    </button>
  )
}

export default function DashboardHero({
  eyebrow,
  title,
  description,
  meta = [],
  actions = [],
  tone = 'student',
  avatar,
  visual,
  className = '',
}: Props) {
  return (
    <section
      className={`db-hero db-hero--${tone} ${className}`.trim()}
      aria-label={title}
    >
      <div className="db-hero__content">
        <div className="db-hero__eyebrow">
          {avatar}
          <span>{eyebrow}</span>
        </div>
        <h1 className="db-hero__title">{title}</h1>
        {description && <p className="db-hero__description">{description}</p>}
        {meta.length > 0 && (
          <ul className="db-hero__meta" aria-label="Dashboard context">
            {meta.filter(Boolean).map((item) => <li key={item}>{item}</li>)}
          </ul>
        )}
        {actions.length > 0 && (
          <div className="db-hero__actions">
            {actions.map((action) => <HeroAction key={action.label} action={action} />)}
          </div>
        )}
      </div>
      {visual && <div className="db-hero__visual" aria-hidden="true">{visual}</div>}
    </section>
  )
}
