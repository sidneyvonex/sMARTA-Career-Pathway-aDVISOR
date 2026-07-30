import { useAuthStore } from '../../store/authStore'
import { useNotificationStore } from '../../store/notificationStore'
import { useLayoutStore } from '../../store/layoutStore'
import { Link, useLocation } from 'react-router-dom'
import { todayLabel } from '../../lib/greeting'
import Avatar from '../common/Avatar'

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

interface PageContext {
  title: string
  parent?: { label: string; to: string }
}

function getPageContext(pathname: string): PageContext {
  if (pathname === '/') return { title: 'Dashboard' }
  if (pathname === '/grades') return { title: 'My grades' }
  if (pathname === '/explore') return { title: 'Explore combinations' }
  if (pathname === '/assessment/results') return {
    title: 'Career profile',
    parent: { label: 'Career quiz', to: '/assessment' },
  }
  if (pathname === '/assessment') return { title: 'Career quiz' }
  if (pathname === '/profile') return { title: 'My profile' }
  if (/^\/counselor\/students\/[^/]+$/.test(pathname)) return {
    title: 'Learner details',
    parent: { label: 'My students', to: '/counselor/students' },
  }
  if (pathname === '/counselor/students') return { title: 'My students' }
  if (pathname === '/counselor/notes') return { title: 'Counsellor notes' }
  if (pathname === '/admin/school') return { title: 'School profile' }
  if (pathname === '/admin/counselors') return { title: 'Counsellors' }
  if (pathname === '/admin/students') return { title: 'Students' }
  if (/^\/parent\/child\/[^/]+$/.test(pathname)) return {
    title: 'Learner profile',
    parent: { label: 'Dashboard', to: '/' },
  }
  if (pathname === '/system-admin/schools') return { title: 'Pilot schools' }
  if (pathname === '/system-admin/users') return { title: 'Users' }
  if (pathname === '/system-admin/audit-log') return { title: 'Audit log' }
  return { title: 'Page not found', parent: { label: 'Dashboard', to: '/' } }
}

export default function Topbar() {
  const { user } = useAuthStore()
  const { unreadCount, drawerOpen, setDrawerOpen } = useNotificationStore()
  const { mobileSidebarOpen, setMobileSidebarOpen } = useLayoutStore()
  const location = useLocation()

  if (!user) return <header className="topbar" role="banner" />

  const page = getPageContext(location.pathname)
  const accountPath = user.role === 'student' ? '/profile' : '/'
  const accountLabel = user.role === 'student' ? 'Open profile' : 'Open account home'

  return (
    <header className="topbar" role="banner">
      <button
        className="topbar__hamburger"
        onClick={() => setMobileSidebarOpen(true)}
        aria-label="Open navigation"
        aria-controls="app-navigation"
        aria-expanded={mobileSidebarOpen}
      >
        {HAMBURGER_ICON}
      </button>

      <div className="topbar__greeting">
        <nav className="topbar__breadcrumbs" aria-label="Breadcrumb">
          <ol>
            <li><Link to="/">Workspace</Link></li>
            {page.parent && <li><Link to={page.parent.to}>{page.parent.label}</Link></li>}
            <li aria-current="page">{page.title}</li>
          </ol>
        </nav>
        <div className="topbar__title-row">
          <div className="topbar__greeting-main">{page.title}</div>
          <span className="topbar__date">{todayLabel()}</span>
        </div>
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

        <Link className="topbar__account-link" to={accountPath} aria-label={accountLabel}>
          <Avatar
            seed={`${user.first_name} ${user.last_name}`}
            size={36}
            shape="squircle"
            className="topbar__avatar"
          />
        </Link>
      </div>
    </header>
  )
}
