import type { CSSProperties } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useLayoutStore } from '../../store/layoutStore'
import { getMobilePrimaryItems, useNavItems } from './navItems'

const MORE_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <circle cx="5" cy="12" r="1.6" fill="currentColor" stroke="none" />
    <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
    <circle cx="19" cy="12" r="1.6" fill="currentColor" stroke="none" />
  </svg>
)

export default function BottomNav() {
  const user = useAuthStore((state) => state.user)
  const { baseNavItems, learnerNavItems } = useNavItems()
  const { mobileMoreOpen, setMobileMoreOpen } = useLayoutStore()
  const location = useLocation()

  if (!user) return null

  const allItems = [...baseNavItems, ...learnerNavItems]
  if (allItems.length === 0) return null

  const primary = getMobilePrimaryItems(user.role, baseNavItems, learnerNavItems)
  const primaryPaths = new Set(primary.map((item) => item.to))
  const overflow = allItems.filter((item) => !primaryPaths.has(item.to))
  const moreActive = overflow.some(
    (item) => item.to !== '/' && location.pathname.startsWith(item.to),
  )

  return (
    <nav
      className="bottom-nav"
      aria-label="Mobile primary navigation"
      style={{ '--bottom-nav-count': primary.length + 1 } as CSSProperties}
    >
      {primary.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/' || allItems.some((other) => other.to.startsWith(`${item.to}/`))}
          className={({ isActive }) => `bottom-nav__item${isActive ? ' active' : ''}`}
        >
          <span className="bottom-nav__icon">{item.icon}</span>
          <span className="bottom-nav__label">{item.short ?? item.label}</span>
        </NavLink>
      ))}
      <button
        type="button"
        className={`bottom-nav__item bottom-nav__more${moreActive || mobileMoreOpen ? ' active' : ''}`}
        onClick={() => setMobileMoreOpen(true)}
        aria-label="More"
        aria-haspopup="dialog"
        aria-controls="mobile-more-sheet"
        aria-expanded={mobileMoreOpen}
      >
        <span className="bottom-nav__icon">{MORE_ICON}</span>
        <span className="bottom-nav__label">More</span>
      </button>
    </nav>
  )
}
