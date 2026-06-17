import { useRef, useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { notificationsApi, type Notification } from '../../api/notifications'
import { useNotificationStore } from '../../store/notificationStore'
import { useAuthStore } from '../../store/authStore'
import { formatRelativeTime } from '../../lib/format'
import '../../styles/notifications.css'

const CHIP_LABELS: Record<string, string> = {
  counselor_note: 'From counselor',
  assessment_submitted: 'Results',
  account: 'Account',
  system: 'System',
}

const NOTIF_ICON: Record<string, { bg: string; icon: JSX.Element }> = {
  counselor_note: {
    bg: 'var(--color-accent)',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>,
  },
  assessment_submitted: {
    bg: 'var(--color-success, #22c55e)',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>,
  },
  account: {
    bg: 'var(--color-info, #3b82f6)',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="12" r="3" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.32 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" /></svg>,
  },
  system: {
    bg: 'var(--color-text-secondary)',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} aria-hidden="true"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>,
  },
}

const DEFAULT_NOTIF_ICON = NOTIF_ICON.system

type Tab = 'all' | 'unread' | 'role'

function roleTabLabel(role: string | undefined) {
  if (role === 'student') return 'From counselor'
  if (role === 'counselor') return 'From students'
  if (role === 'parent') return 'About my child'
  return null
}

function roleTabFilter(notif: Notification, role: string | undefined) {
  if (role === 'student') return notif.type === 'counselor_note'
  if (role === 'counselor') return notif.type === 'assessment_submitted'
  if (role === 'parent') return notif.type === 'assessment_submitted'
  return false
}

export default function NotificationPanel() {
  const { drawerOpen, setDrawerOpen } = useNotificationStore()
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const closeRef = useRef<HTMLButtonElement>(null)
  const [activeTab, setActiveTab] = useState<Tab>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.getList().then((r) => r.data.data),
    enabled: drawerOpen,
    staleTime: 0,
  })

  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notification-unread-count'] })
    },
    onError: () => toast.error('Failed to mark notification as read.'),
  })

  const markAllMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notification-unread-count'] })
      toast.success('All notifications marked as read.')
    },
    onError: () => toast.error('Failed to mark notifications as read.'),
  })

  useEffect(() => {
    if (drawerOpen) closeRef.current?.focus()
  }, [drawerOpen])

  useEffect(() => {
    if (!drawerOpen) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setDrawerOpen(false) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [drawerOpen, setDrawerOpen])

  useEffect(() => {
    if (drawerOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [drawerOpen])

  const all = data ?? []
  const unread = all.filter((n) => !n.read)
  const roleLabel = roleTabLabel(user?.role)

  const displayed =
    activeTab === 'unread' ? unread
    : activeTab === 'role' ? all.filter((n) => roleTabFilter(n, user?.role))
    : all

  return (
    <>
      <div
        className={`notification-overlay${drawerOpen ? ' open' : ''}`}
        onClick={() => setDrawerOpen(false)}
        aria-hidden="true"
      />
      <aside
        className={`notification-drawer${drawerOpen ? ' open' : ''}`}
        role="dialog"
        aria-label="Notifications"
      >
        {/* Header */}
        <div className="notification-drawer__header">
          <h2>Notifications</h2>
          <button
            ref={closeRef}
            className="notification-drawer__close"
            onClick={() => setDrawerOpen(false)}
            aria-label="Close notifications"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="notification-panel__tabs">
          <button
            className={`notification-panel__tab${activeTab === 'all' ? ' notification-panel__tab--active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All
            {all.length > 0 && (
              <span className="notification-panel__tab-badge">{all.length}</span>
            )}
          </button>
          <button
            className={`notification-panel__tab${activeTab === 'unread' ? ' notification-panel__tab--active' : ''}`}
            onClick={() => setActiveTab('unread')}
          >
            Unread
            {unread.length > 0 && (
              <span className="notification-panel__tab-badge">{unread.length}</span>
            )}
          </button>
          {roleLabel && (
            <button
              className={`notification-panel__tab${activeTab === 'role' ? ' notification-panel__tab--active' : ''}`}
              onClick={() => setActiveTab('role')}
            >
              {roleLabel}
            </button>
          )}
        </div>

        {/* Mark all */}
        {unread.length > 0 && (
          <div className="notification-drawer__actions">
            <button
              className="notification-drawer__mark-all"
              onClick={() => markAllMutation.mutate()}
              disabled={markAllMutation.isPending}
            >
              {markAllMutation.isPending ? 'Marking…' : 'Mark all as read'}
            </button>
          </div>
        )}

        {/* List */}
        <ul className="notification-drawer__list" aria-label="Notification list">
          {isLoading && (
            <li style={{ padding: '1rem 1.5rem', color: 'var(--color-text-secondary)' }}>
              Loading…
            </li>
          )}
          {!isLoading && displayed.length === 0 && (
            <li className="notification-drawer__empty">No notifications here.</li>
          )}
          {displayed.map((notif) => (
            <li key={notif.id} className={`notification-item${notif.read ? '' : ' unread'}`}>
              <button
                className="notification-item__btn"
                onClick={() => { if (!notif.read) markReadMutation.mutate(notif.id) }}
                aria-label={notif.read ? undefined : `Mark as read: ${notif.message}`}
              >
                {!notif.read && <span className="notification-item__dot" aria-hidden="true" />}
                <div
                  className="notification-item__avatar"
                  aria-hidden="true"
                  style={{ background: (NOTIF_ICON[notif.type] ?? DEFAULT_NOTIF_ICON).bg }}
                >
                  {(NOTIF_ICON[notif.type] ?? DEFAULT_NOTIF_ICON).icon}
                </div>
                <div className="notification-item__body">
                  <p className="notification-item__message">{notif.message}</p>
                  <span
                    className={`notification-type-chip notification-type-chip--${notif.type}`}
                  >
                    {CHIP_LABELS[notif.type] ?? notif.type}
                  </span>
                  <span className="notification-item__time">{formatRelativeTime(notif.created_at)}</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </>
  )
}
