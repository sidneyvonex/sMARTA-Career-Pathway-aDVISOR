import { useNotificationStore } from '../../../store/notificationStore'
import type { Notification } from '../../../api/notifications'

const BELL_ICON = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
)

function formatTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return new Date(iso).toLocaleDateString('en-KE', { day: 'numeric', month: 'short' })
}

interface Props {
  notifications: Notification[]
}

export default function ActivityFeed({ notifications }: Props) {
  const { setDrawerOpen } = useNotificationStore()
  const recent = notifications.slice(0, 3)

  return (
    <div className="dashboard-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <p className="dashboard-card__title" style={{ marginBottom: 0 }}>What's new</p>
        <button className="activity-feed__see-all" onClick={() => setDrawerOpen(true)}>
          See all
        </button>
      </div>

      {recent.length === 0 ? (
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          No recent activity.
        </p>
      ) : (
        <div className="activity-feed">
          {recent.map((n) => (
            <div key={n.id} className="activity-item">
              <div className="activity-item__icon">{BELL_ICON}</div>
              <div className="activity-item__body">
                <p className="activity-item__text">{n.message}</p>
                <span className="activity-item__time">{formatTime(n.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
