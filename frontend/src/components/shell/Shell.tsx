import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import NotificationPanel from './NotificationPanel'
import { useLayoutStore } from '../../store/layoutStore'
import '../../styles/shell.css'

export default function Shell() {
  const { sidebarCollapsed, mobileSidebarOpen, setMobileSidebarOpen } = useLayoutStore()

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
