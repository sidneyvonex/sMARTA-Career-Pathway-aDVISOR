import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import NotificationPanel from './NotificationPanel'
import ErrorBoundary from '../common/ErrorBoundary'
import { useLayoutStore } from '../../store/layoutStore'
import '../../styles/shell.css'
import '../../styles/role-dashboard.css'

interface ShellProps {
  children?: ReactNode
}

export default function Shell({ children }: ShellProps) {
  const { sidebarCollapsed, mobileSidebarOpen, setMobileSidebarOpen } = useLayoutStore()
  const [isOnline, setIsOnline] = useState(() => navigator.onLine)
  const location = useLocation()

  useEffect(() => {
    if (mobileSidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [mobileSidebarOpen])

  useEffect(() => {
    const updateConnection = () => setIsOnline(navigator.onLine)
    window.addEventListener('online', updateConnection)
    window.addEventListener('offline', updateConnection)
    return () => {
      window.removeEventListener('online', updateConnection)
      window.removeEventListener('offline', updateConnection)
    }
  }, [])

  useEffect(() => {
    if (!mobileSidebarOpen) return
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileSidebarOpen(false)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [mobileSidebarOpen, setMobileSidebarOpen])

  return (
    <div className={`shell${sidebarCollapsed ? ' shell--collapsed' : ''}`}>
      <a className="shell__skip-link" href="#main-content">Skip to main content</a>
      <Sidebar />

      <button
        type="button"
        tabIndex={mobileSidebarOpen ? 0 : -1}
        className={`shell__mobile-overlay${mobileSidebarOpen ? ' shell__mobile-overlay--open' : ''}`}
        onClick={() => setMobileSidebarOpen(false)}
        aria-label="Close navigation overlay"
      />

      <div className="shell__main">
        <Topbar />
        <main className="shell__content" id="main-content">
          <div className="shell__content-inner" data-testid="shell-content-inner">
            <ErrorBoundary resetKey={location.pathname}>
              {children ?? <Outlet />}
            </ErrorBoundary>
          </div>
        </main>
      </div>

      {!isOnline && (
        <div className="shell__offline-status" role="status">
          <span className="shell__offline-dot" aria-hidden="true" />
          <span>Offline. Saved pages may remain available, but updates need a connection.</span>
        </div>
      )}

      <NotificationPanel />
    </div>
  )
}
