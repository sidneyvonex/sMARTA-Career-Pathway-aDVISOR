import type { ReactNode } from 'react'
import '../../../styles/management.css'

interface ManagementToolbarProps {
  className?: string
  resultCount: string
  search: ReactNode
  filters?: ReactNode
  pageAction?: ReactNode
  bulkActions?: ReactNode
}

export default function ManagementToolbar({
  className,
  resultCount,
  search,
  filters,
  pageAction,
  bulkActions,
}: ManagementToolbarProps) {
  return (
    <div className={`management-toolbar${className ? ` ${className}` : ''}`}>
      <div className="management-toolbar__main">
        <div className="management-toolbar__search">{search}</div>
        {filters && <div className="management-toolbar__filters">{filters}</div>}
        <p className="management-toolbar__result-count" aria-live="polite">{resultCount}</p>
      </div>
      {(bulkActions || pageAction) && (
        <div className="management-toolbar__actions">
          {bulkActions}
          {pageAction}
        </div>
      )}
    </div>
  )
}
