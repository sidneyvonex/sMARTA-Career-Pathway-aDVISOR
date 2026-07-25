import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import NotificationPanel from './NotificationPanel'
import { useLayoutStore } from '../../store/layoutStore'
import '../../styles/shell.css'

interface ShellProps {
  children?: ReactNode
}

export default function Shell({ children }: ShellProps) {
  const { sidebarCollapsed, mobileSidebarOpen, setMobileSidebarOpen } = useLayoutStore()

  useEffect(() => {
    if (mobileSidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [mobileSidebarOpen])

  return (
    <div className={`shell${sidebarCollapsed ? ' shell--collapsed' : ''}`}>
      <Sidebar />

      <div
        className={`shell__mobile-overlay${mobileSidebarOpen ? ' shell__mobile-overlay--open' : ''}`}
        onClick={() => setMobileSidebarOpen(false)}
        aria-hidden="true"
      />

      <div className="shell__main">
        <Topbar />
        <main className="shell__content" id="main-content">
          {children ?? <Outlet />}
        </main>
      </div>

      <NotificationPanel />
    </div>
  )
}
