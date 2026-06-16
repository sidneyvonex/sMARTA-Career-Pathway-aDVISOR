import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useNotificationStore } from '../../store/notificationStore'
import '../../styles/notifications.css'

export default function Navbar() {
  const { user } = useAuthStore()
  const { unreadCount, drawerOpen, setDrawerOpen } = useNotificationStore()

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <NavLink to="/" className="navbar__brand">
        <img src="/logo.png" alt="" aria-hidden="true" />
        Smarta Shauri
      </NavLink>

      {user?.role === 'student' && (
        <ul className="navbar__links">
          <li><NavLink to="/profile">Profile</NavLink></li>
          <li><NavLink to="/grades">Grades</NavLink></li>
          <li><NavLink to="/assessment">Assessment</NavLink></li>
        </ul>
      )}

      <div className="navbar__right">
        <button
          className="notification-bell"
          onClick={() => setDrawerOpen(true)}
          aria-label="Notifications"
          aria-haspopup="dialog"
          aria-expanded={drawerOpen}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {unreadCount > 0 && (
            <span className="notification-badge" role="status" aria-label={`${unreadCount} unread notifications`}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </div>
    </nav>
  )
}
