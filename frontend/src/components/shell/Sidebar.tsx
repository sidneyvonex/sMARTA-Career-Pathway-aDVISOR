import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useLayoutStore } from '../../store/layoutStore'
import { useLogout } from '../../hooks/useLogout'
import { useNavItems } from './navItems'
import Avatar from '../common/Avatar'

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

const LOGOUT_ICON = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
  </svg>
)

const CLOSE_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
  </svg>
)

export default function Sidebar() {
  const { user } = useAuthStore()
  const { sidebarCollapsed, mobileSidebarOpen, toggleSidebar, setMobileSidebarOpen } = useLayoutStore()
  const { baseNavItems, learnerNavItems } = useNavItems()
  const handleLogout = useLogout()

  if (!user) return <aside className="sidebar" aria-label="Main navigation" />

  const allNavItems = [...baseNavItems, ...learnerNavItems]
  const collapsed = sidebarCollapsed
  const roleLabel = user.role.replace('_', ' ')

  return (
    <aside
      id="app-navigation"
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
          type="button"
          className="sidebar__mobile-close"
          tabIndex={mobileSidebarOpen ? 0 : -1}
          onClick={() => setMobileSidebarOpen(false)}
          aria-label="Close navigation"
        >
          {CLOSE_ICON}
        </button>
        <button
          className="sidebar__toggle"
          onClick={() => { toggleSidebar(); setMobileSidebarOpen(false) }}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? CHEVRON_RIGHT : CHEVRON_LEFT}
        </button>
      </div>

      {/* Nav */}
      <nav className="sidebar__nav" aria-label="Primary">
        {baseNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/' || allNavItems.some((other) => other.to.startsWith(`${item.to}/`))}
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

        {learnerNavItems.length > 0 && (
          <>
            <p className="sidebar__section-label">Your learners</p>
            {learnerNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `sidebar__nav-item${isActive ? ' active' : ''}`
                }
                onClick={() => setMobileSidebarOpen(false)}
              >
                <span className="sidebar__nav-icon">{item.icon}</span>
                <span className="sidebar__nav-label">{item.label}</span>
                {item.badge && <span className="sidebar__badge sidebar__badge--soft">{item.badge}</span>}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* Footer */}
      <div className="sidebar__footer">
        <Avatar
          seed={`${user.first_name} ${user.last_name}`}
          size={40}
          shape="squircle"
          className="sidebar__avatar"
        />
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
