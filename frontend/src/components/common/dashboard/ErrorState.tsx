interface Props {
  title?: string
  description: string
  onRetry?: () => void
}

export default function ErrorState({
  title = 'This section could not load',
  description,
  onRetry,
}: Props) {
  return (
    <section className="db-state db-state--error" role="alert">
      <span className="db-state__mark" aria-hidden="true">↻</span>
      <h3>{title}</h3>
      <p>{description}</p>
      {onRetry && (
        <button type="button" className="db-state__action" onClick={onRetry}>Try again</button>
      )}
    </section>
  )
}
