import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import NotificationPanel from './NotificationPanel'
import { useLayoutStore } from '../../store/layoutStore'
import '../../styles/shell.css'

export default function Shell() {
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
          <Outlet />
        </main>
      </div>

      <NotificationPanel />
    </div>
  )
}
