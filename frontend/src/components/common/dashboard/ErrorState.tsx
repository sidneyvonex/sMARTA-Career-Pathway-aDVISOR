import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface Props {
  title?: string
  description: string
  onRetry?: () => void
  actionLabel?: string
  secondaryAction?: {
    label: string
    to: string
  }
  // The default ↻ mark reads as "retry", which suits load errors. Pass a
  // different glyph for states where retrying makes no sense (e.g. 404).
  mark?: ReactNode
}

export default function ErrorState({
  title = 'This section could not load',
  description,
  onRetry,
  actionLabel = 'Try again',
  secondaryAction,
  mark = '↻',
}: Props) {
  return (
    <section className="db-state db-state--error" role="alert">
      <span className="db-state__mark" aria-hidden="true">{mark}</span>
      <h3>{title}</h3>
      <p>{description}</p>
      {(onRetry || secondaryAction) && (
        <div className="db-state__actions">
          {onRetry && (
            <button type="button" className="db-state__action" onClick={onRetry}>{actionLabel}</button>
          )}
          {secondaryAction && (
            <Link className="db-state__secondary" to={secondaryAction.to}>
              {secondaryAction.label}
            </Link>
          )}
        </div>
      )}
    </section>
  )
}
