import { useAuthStore } from '../../store/authStore'
import { useNotificationStore } from '../../store/notificationStore'
import { useLayoutStore } from '../../store/layoutStore'
import { greeting, todayLabel } from '../../lib/greeting'
import { initials } from '../../lib/format'

const BELL_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
)

const HAMBURGER_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
  </svg>
)

export default function Topbar() {
  const { user } = useAuthStore()
  const { unreadCount, drawerOpen, setDrawerOpen } = useNotificationStore()
  const { setMobileSidebarOpen } = useLayoutStore()

  if (!user) return <header className="topbar" role="banner" />

  return (
    <header className="topbar" role="banner">
      <button
        className="topbar__hamburger"
        onClick={() => setMobileSidebarOpen(true)}
        aria-label="Open navigation"
      >
        {HAMBURGER_ICON}
      </button>

      <div className="topbar__greeting">
        <div className="topbar__greeting-main">{greeting(user.first_name)}</div>
        <div className="topbar__greeting-sub">{todayLabel()}</div>
      </div>

      <div className="topbar__actions">
        <button
          className="topbar__icon-btn"
          onClick={() => setDrawerOpen(true)}
          aria-label="Notifications"
          aria-haspopup="dialog"
          aria-expanded={drawerOpen}
        >
          {BELL_ICON}
          {unreadCount > 0 && (
            <span className="notification-badge" role="status" aria-label={`${unreadCount} unread`}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        <div
          className="topbar__avatar"
          role="img"
          aria-label={`${user.first_name} ${user.last_name}`}
        >
          {initials(user.first_name, user.last_name)}
        </div>
      </div>
    </header>
  )
}
