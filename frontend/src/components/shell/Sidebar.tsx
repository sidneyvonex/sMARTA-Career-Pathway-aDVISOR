import { NavLink, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../store/authStore'
import { useLayoutStore } from '../../store/layoutStore'
import { authApi, type User } from '../../api/auth'
import { initials } from '../../lib/format'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  badge?: string
}

const CHEVRON_LEFT = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
  </svg>
)

const CHEVRON_RIGHT = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
  </svg>
)

const ICONS = {
  grid: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>,
  bar: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12h3m0 0V6m0 6v6m4-6h3m0 0V9m0 3v3m4-3h3m0 0V3m0 9v9" /></svg>,
  clock: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="12" r="9" /><path strokeLinecap="round" d="M12 7v5l3 3" /></svg>,
  clipboard: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
  person: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="8" r="4" /><path strokeLinecap="round" d="M4 20c0-4 3.6-7 8-7s8 3 8 7" /></svg>,
  gear: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="12" r="3" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" /></svg>,
  users: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path strokeLinecap="round" d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" /></svg>,
  child: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="7" r="4" /><path strokeLinecap="round" d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" /></svg>,
  chart: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M7 20V10m5 10V4m5 16v-7" /></svg>,
}

function getNavItems(role: User['role']): NavItem[] {
  if (role === 'student') {
    return [
      { to: '/', label: 'Home', icon: ICONS.grid },
      { to: '/grades', label: 'My Grades', icon: ICONS.bar },
      { to: '/assessment/results', label: 'My Results', icon: ICONS.clock },
      { to: '/assessment', label: 'Career Quiz', icon: ICONS.clipboard },
      { to: '/profile', label: 'My Profile', icon: ICONS.person },
    ]
  }
  if (role === 'counselor') {
    return [
      { to: '/', label: 'Home', icon: ICONS.grid },
      { to: '/students', label: 'My Students', icon: ICONS.users },
    ]
  }
  if (role === 'parent') {
    return [
      { to: '/', label: 'Home', icon: ICONS.grid },
      { to: '/child', label: 'My Child', icon: ICONS.child },
      { to: '/progress', label: 'Progress', icon: ICONS.chart },
    ]
  }
  return [{ to: '/', label: 'Home', icon: ICONS.grid }]
}

const LOGOUT_ICON = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
  </svg>
)

export default function Sidebar() {
  const { user, clearUser } = useAuthStore()
  const { sidebarCollapsed, mobileSidebarOpen, toggleSidebar, setMobileSidebarOpen } = useLayoutStore()
  const navigate = useNavigate()

  if (!user) return <aside className="sidebar" aria-label="Main navigation" />

  const navItems = getNavItems(user.role)
  const collapsed = sidebarCollapsed
  const roleLabel = user.role.replace('_', ' ')

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch { /* cookie cleared regardless */ }
    clearUser()
    navigate('/login')
    toast.success('Logged out.')
  }

  return (
    <aside
      className={[
        'sidebar',
        collapsed ? 'sidebar--collapsed' : '',
        mobileSidebarOpen ? 'sidebar--mobile-open' : '',
      ].join(' ')}
      aria-label="Main navigation"
    >
      {/* Header */}
      <div className="sidebar__header">
        <img src="/logo.png" alt="" className="sidebar__logo" aria-hidden="true" />
        <span className="sidebar__app-name">Smarta Shauri</span>
        <button
          className="sidebar__toggle"
          onClick={() => { toggleSidebar(); setMobileSidebarOpen(false) }}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? CHEVRON_RIGHT : CHEVRON_LEFT}
        </button>
      </div>

      {/* Nav */}
      <nav className="sidebar__nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `sidebar__nav-item${isActive ? ' active' : ''}`
            }
            onClick={() => setMobileSidebarOpen(false)}
          >
            <span className="sidebar__nav-icon">{item.icon}</span>
            <span className="sidebar__nav-label">{item.label}</span>
            {item.badge && <span className="sidebar__badge">{item.badge}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar__footer">
        <div className="sidebar__avatar" aria-hidden="true">
          {initials(user.first_name, user.last_name)}
        </div>
        <div className="sidebar__user-info">
          <div className="sidebar__user-name">{user.first_name} {user.last_name}</div>
          <div className="sidebar__user-role">{roleLabel}</div>
        </div>
        <button
          className="sidebar__toggle"
          onClick={handleLogout}
          aria-label="Log out"
          title="Log out"
        >
          {LOGOUT_ICON}
        </button>
      </div>
    </aside>
  )
}
