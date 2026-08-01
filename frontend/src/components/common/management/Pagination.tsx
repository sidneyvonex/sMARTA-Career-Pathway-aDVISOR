import type { PaginationState } from './types'
import '../../../styles/management.css'

interface PaginationProps {
  state: PaginationState
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: PaginationState['pageSize']) => void
}

const allowedPageSizes: PaginationState['pageSize'][] = [10, 25, 50]

export default function Pagination({ state, onPageChange, onPageSizeChange }: PaginationProps) {
  const pageCount = Math.max(1, Math.ceil(state.total / state.pageSize))
  const currentPage = Math.min(Math.max(1, state.page), pageCount)

  return (
    <nav className="management-pagination" aria-label="Table pagination">
      <label className="management-pagination__size">
        <span>Rows per page</span>
        <select
          value={state.pageSize}
          onChange={(event) => {
            const nextSize = Number(event.target.value) as PaginationState['pageSize']
            if (!allowedPageSizes.includes(nextSize)) return
            onPageSizeChange(nextSize)
            if (currentPage !== 1) onPageChange(1)
          }}
        >
          {allowedPageSizes.map(size => <option key={size} value={size}>{size}</option>)}
        </select>
      </label>
      <p className="management-pagination__summary" aria-live="polite">
        Page {currentPage} of {pageCount}
      </p>
      <div className="management-pagination__controls">
        <button
          type="button"
          className="btn-ghost"
          aria-label="Previous page"
          disabled={currentPage <= 1}
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        >
          Previous
        </button>
        <button
          type="button"
          className="btn-ghost"
          aria-label="Next page"
          disabled={currentPage >= pageCount}
          onClick={() => onPageChange(Math.min(pageCount, currentPage + 1))}
        >
          Next
        </button>
      </div>
    </nav>
  )
}
