import type { ReactNode } from 'react'
import RowActionMenu from './RowActionMenu'
import type { ManagementAction, ManagementColumn } from './types'
import '../../../styles/management.css'

interface ManagementTableProps<T> {
  ariaLabel: string
  records: T[]
  columns: ManagementColumn<T>[]
  getKey: (record: T) => string | number
  getRecordLabel: (record: T) => string
  getPrimaryAction: (record: T) => ManagementAction
  getSecondaryActions: (record: T) => ManagementAction[]
  empty: ReactNode
}

export default function ManagementTable<T>({
  ariaLabel,
  records,
  columns,
  getKey,
  getRecordLabel,
  getPrimaryAction,
  getSecondaryActions,
  empty,
}: ManagementTableProps<T>) {
  return (
    <div className="management-table-wrap">
      <table className="management-table" aria-label={ariaLabel}>
        <thead>
          <tr>
            {columns.map(column => (
              <th key={column.key} scope="col" data-align={column.align ?? 'start'}>
                {column.label}
              </th>
            ))}
            <th scope="col" data-align="end">Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.length === 0 ? (
            <tr className="management-table__empty-row">
              <td colSpan={columns.length + 1}>{empty}</td>
            </tr>
          ) : records.map(record => {
            const recordLabel = getRecordLabel(record)
            const primaryAction = getPrimaryAction(record)
            const secondaryActions = getSecondaryActions(record)
            return (
              <tr key={getKey(record)}>
                {columns.map(column => (
                  <td
                    key={column.key}
                    data-label={column.label}
                    data-priority={column.priority ?? 'secondary'}
                    data-align={column.align ?? 'start'}
                  >
                    <div className="management-table__cell-content">
                      {column.render(record)}
                    </div>
                  </td>
                ))}
                <td data-label="Actions" data-priority="action" data-align="end">
                  <div className="management-table__actions">
                    <button
                      type="button"
                      className="management-table__primary-action"
                      aria-label={primaryAction.label}
                      disabled={primaryAction.disabled}
                      onClick={primaryAction.onSelect}
                    >
                      {primaryAction.shortLabel ?? primaryAction.label}
                    </button>
                    {secondaryActions.length > 0 && (
                      <RowActionMenu
                        recordLabel={recordLabel}
                        actions={secondaryActions}
                        disabled={primaryAction.disabled}
                      />
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
