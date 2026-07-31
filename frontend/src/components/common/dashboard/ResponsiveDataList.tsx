import type { ReactNode } from 'react'

export interface DataColumn<T> {
  key: string
  label: string
  render: (item: T) => ReactNode
  align?: 'start' | 'center' | 'end'
}

interface Props<T> {
  ariaLabel: string
  items: T[]
  columns: DataColumn<T>[]
  getKey: (item: T) => string | number
  empty?: ReactNode
}

export default function ResponsiveDataList<T>({
  ariaLabel,
  items,
  columns,
  getKey,
  empty,
}: Props<T>) {
  if (items.length === 0 && empty) return <>{empty}</>

  return (
    <div className="db-data-list">
      <table aria-label={ariaLabel}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" data-align={column.align ?? 'start'}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={getKey(item)}>
              {columns.map((column) => (
                <td
                  key={column.key}
                  data-label={column.label}
                  data-align={column.align ?? 'start'}
                >
                  {column.render(item)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
