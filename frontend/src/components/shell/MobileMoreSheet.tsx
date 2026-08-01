import { useEffect, useRef } from 'react'
import { NavLink } from 'react-router-dom'
import { useInstallPrompt } from '../../hooks/useInstallPrompt'
import { useLogout } from '../../hooks/useLogout'
import { useAuthStore } from '../../store/authStore'
import { useLayoutStore } from '../../store/layoutStore'
import { useNotificationStore } from '../../store/notificationStore'
import Avatar from '../common/Avatar'
import { useNavItems } from './navItems'

const CLOSE_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
  </svg>
)

const BELL_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 00-4-5.7V5a2 2 0 10-4 0v.3A6 6 0 006 11v3.2a2 2 0 01-.6 1.4L4 17h16M14.7 17a3 3 0 01-5.4 0" />
  </svg>
)

const LOGOUT_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
  </svg>
)

interface MobileMoreSheetProps {
  isOnline: boolean
}

export default function MobileMoreSheet({ isOnline }: MobileMoreSheetProps) {
  const user = useAuthStore((state) => state.user)
  const { mobileMoreOpen, setMobileMoreOpen } = useLayoutStore()
  const setDrawerOpen = useNotificationStore((state) => state.setDrawerOpen)
  const { baseNavItems, learnerNavItems } = useNavItems()
  const { canInstall, promptInstall } = useInstallPrompt()
  const logout = useLogout()
  const dialogRef = useRef<HTMLElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const wasOpen = useRef(false)

  const close = () => setMobileMoreOpen(false)

  useEffect(() => {
    if (mobileMoreOpen) {
      document.body.style.overflow = 'hidden'
      closeRef.current?.focus()
    } else {
      document.body.style.overflow = ''
      if (wasOpen.current) {
        document.querySelector<HTMLButtonElement>('.bottom-nav__more')?.focus()
      }
    }
    wasOpen.current = mobileMoreOpen
    return () => { document.body.style.overflow = '' }
  }, [mobileMoreOpen])

  useEffect(() => {
    if (!mobileMoreOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        close()
        return
      }
      if (event.key !== 'Tab' || !dialogRef.current) return

      const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ))
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileMoreOpen])

  useEffect(() => {
    const tabletNavigation = window.matchMedia('(min-width: 768px)')
    const handleViewportChange = (event: MediaQueryListEvent) => {
      if (event.matches) setMobileMoreOpen(false)
    }

    tabletNavigation.addEventListener('change', handleViewportChange)
    if (tabletNavigation.matches) setMobileMoreOpen(false)
    return () => tabletNavigation.removeEventListener('change', handleViewportChange)
  }, [setMobileMoreOpen])

  if (!mobileMoreOpen || !user) return null

  const allItems = [...baseNavItems, ...learnerNavItems]

  return (
    <div className="mobile-more-layer">
      <button
        type="button"
        className="mobile-more__overlay"
        onClick={close}
        tabIndex={-1}
        aria-hidden="true"
      />
      <aside
        ref={dialogRef}
        id="mobile-more-sheet"
        className="mobile-more"
        role="dialog"
        aria-modal="true"
        aria-label="More navigation and account"
      >
        <header className="mobile-more__header">
          <div className="mobile-more__identity">
            <Avatar
              seed={`${user.first_name} ${user.last_name}`}
              size={44}
              shape="squircle"
            />
            <div>
              <strong>{user.first_name} {user.last_name}</strong>
              <span>{user.role.replace('_', ' ')}</span>
            </div>
          </div>
          <button ref={closeRef} type="button" className="mobile-more__close" onClick={close} aria-label="Close More menu">
            {CLOSE_ICON}
          </button>
        </header>

        <nav className="mobile-more__nav" aria-label="All account destinations">
          {allItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/' || allItems.some((other) => other.to.startsWith(`${item.to}/`))}
              className={({ isActive }) => `mobile-more__nav-item${isActive ? ' active' : ''}`}
              onClick={close}
            >
              <span className="mobile-more__nav-icon">{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && <span className="mobile-more__badge">{item.badge}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="mobile-more__actions">
          <button
            type="button"
            className="mobile-more__action"
            onClick={() => {
              close()
              setDrawerOpen(true)
            }}
          >
            {BELL_ICON}
            <span>Notifications</span>
          </button>
          {canInstall && (
            <button type="button" className="mobile-more__action" onClick={promptInstall}>
              <img src="/logo.png" alt="" aria-hidden="true" />
              <span>Install Smarta Shauri</span>
            </button>
          )}
          <p className="mobile-more__status" role="status">
            <span className={isOnline ? 'online' : 'offline'} aria-hidden="true" />
            {isOnline ? 'Online and ready' : 'Offline. Updates need a connection.'}
          </p>
          <button type="button" className="mobile-more__action mobile-more__logout" onClick={logout}>
            {LOGOUT_ICON}
            <span>Log out</span>
          </button>
        </div>
      </aside>
    </div>
  )
}
