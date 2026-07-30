interface Props {
  label?: string
  rows?: number
  variant?: 'page' | 'metrics' | 'list'
}

export default function LoadingSkeleton({
  label = 'Loading dashboard',
  rows = 3,
  variant = 'page',
}: Props) {
  return (
    <div className={`db-loading db-loading--${variant}`} role="status" aria-label={label}>
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, index) => (
        <div className="db-loading__row" key={index} aria-hidden="true">
          <span />
          <span />
        </div>
      ))}
    </div>
  )
}
