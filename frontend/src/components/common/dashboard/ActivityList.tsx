import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export interface ActivityItem {
  id: string | number
  title: string
  detail?: string
  time?: string
  to?: string
  onClick?: () => void
  icon?: ReactNode
}

interface Props {
  items: ActivityItem[]
  ariaLabel?: string
  empty?: ReactNode
}

function ActivityContent({ item }: { item: ActivityItem }) {
  return (
    <>
      {item.icon && <span className="db-activity__icon" aria-hidden="true">{item.icon}</span>}
      <span className="db-activity__body">
        <strong>{item.title}</strong>
        {item.detail && <span>{item.detail}</span>}
      </span>
      {item.time && <time className="db-activity__time">{item.time}</time>}
    </>
  )
}

export default function ActivityList({
  items,
  ariaLabel = 'Recent activity',
  empty,
}: Props) {
  if (items.length === 0) return empty ? <>{empty}</> : null

  return (
    <ul className="db-activity" aria-label={ariaLabel}>
      {items.map((item) => (
        <li key={item.id}>
          {item.to ? (
            <Link to={item.to} className="db-activity__item"><ActivityContent item={item} /></Link>
          ) : item.onClick ? (
            <button type="button" className="db-activity__item" onClick={item.onClick}>
              <ActivityContent item={item} />
            </button>
          ) : (
            <div className="db-activity__item"><ActivityContent item={item} /></div>
          )}
        </li>
      ))}
    </ul>
  )
}
