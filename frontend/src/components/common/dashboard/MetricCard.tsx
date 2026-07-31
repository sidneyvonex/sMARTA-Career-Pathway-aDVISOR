import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { SurfaceTone } from './types'

interface Props {
  label: string
  value: ReactNode
  detail?: ReactNode
  icon?: ReactNode
  tone?: SurfaceTone
  to?: string
  onClick?: () => void
}

export default function MetricCard({
  label,
  value,
  detail,
  icon,
  tone = 'neutral',
  to,
  onClick,
}: Props) {
  const className = `db-metric db-metric--${tone}${to || onClick ? ' db-metric--interactive' : ''}`
  const ariaLabel = `${label}: ${String(value)}`
  const content = (
    <>
      <div className="db-metric__top">
        <span className="db-metric__label">{label}</span>
        {icon && <span className="db-metric__icon" aria-hidden="true">{icon}</span>}
      </div>
      <strong className="db-metric__value">{value}</strong>
      {detail && <span className="db-metric__detail">{detail}</span>}
    </>
  )

  if (to) {
    return <Link to={to} className={className} aria-label={ariaLabel}>{content}</Link>
  }

  if (onClick) {
    return <button type="button" className={className} aria-label={ariaLabel} onClick={onClick}>{content}</button>
  }

  return <article className={className} aria-label={ariaLabel}>{content}</article>
}
