import type { ReactNode } from 'react'
import ErrorState from '../dashboard/ErrorState'
import LoadingSkeleton from '../dashboard/LoadingSkeleton'
import SectionHeader from '../dashboard/SectionHeader'

interface ManagementPageError {
  title: string
  description: string
}

interface ManagementPageProps {
  title: string
  eyebrow?: string
  description: ReactNode
  pageAction?: ReactNode
  toolbar?: ReactNode
  loading: boolean
  error?: ManagementPageError
  onRetry?: () => void
  errorActionLabel?: string
  children: ReactNode
}

export default function ManagementPage({
  title,
  eyebrow,
  description,
  pageAction,
  toolbar,
  loading,
  error,
  onRetry,
  errorActionLabel,
  children,
}: ManagementPageProps) {
  return (
    <main className="management-page">
      <div className="management-page__heading">
        <SectionHeader
          eyebrow={eyebrow}
          title={title}
          titleAs="h1"
          description={description}
          aside={pageAction}
          className="management-page__section-header"
        />
      </div>

      {loading ? (
        <LoadingSkeleton label={`Loading ${title}`} rows={5} variant="list" />
      ) : error ? (
        <ErrorState
          title={error.title}
          description={error.description}
          onRetry={onRetry}
          actionLabel={errorActionLabel}
        />
      ) : (
        <>
          {toolbar}
          <div className="management-page__body">{children}</div>
        </>
      )}
    </main>
  )
}
