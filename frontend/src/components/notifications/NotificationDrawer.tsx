import { useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { notificationsApi, Notification } from '../../api/notifications'
import { useNotificationStore } from '../../store/notificationStore'

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  return date.toLocaleDateString('en-KE', { day: 'numeric', month: 'short' })
}

export default function NotificationDrawer() {
  const { drawerOpen, setDrawerOpen } = useNotificationStore()
  const qc = useQueryClient()
  const closeRef = useRef<HTMLButtonElement>(null)

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
    onError: () => {
      toast.error('Failed to mark notification as read.')
    },
  })

  const markAllMutation = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notification-unread-count'] })
      toast.success('All notifications marked as read.')
    },
    onError: () => {
      toast.error('Failed to mark notifications as read.')
    },
  })

  function handleItemClick(notif: Notification) {
    if (!notif.read) {
      markReadMutation.mutate(notif.id)
    }
  }

  // Move focus to close button when drawer opens
  useEffect(() => {
    if (drawerOpen) closeRef.current?.focus()
  }, [drawerOpen])

  // Close on Escape key
  useEffect(() => {
    if (!drawerOpen) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setDrawerOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [drawerOpen, setDrawerOpen])

  const hasUnread = (data ?? []).some((n) => !n.read)

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
        aria-modal="true"
        aria-label="Notifications"
      >
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

        {hasUnread && (
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

        <ul className="notification-drawer__list" aria-label="Notification list">
          {isLoading && (
            <li style={{ padding: '1rem 1.5rem', color: 'var(--color-text-secondary)' }}>
              Loading…
            </li>
          )}
          {!isLoading && (!data || data.length === 0) && (
            <li className="notification-drawer__empty">
              No notifications yet.
            </li>
          )}
          {data?.map((notif) => (
            <li key={notif.id} className={`notification-item${notif.read ? '' : ' unread'}`}>
              <button
                className="notification-item__btn"
                onClick={() => handleItemClick(notif)}
                style={{ all: 'unset', display: 'flex', width: '100%', gap: 'var(--space-2, 0.5rem)', alignItems: 'flex-start', cursor: notif.read ? 'default' : 'pointer' }}
                aria-label={notif.read ? undefined : `Mark as read: ${notif.message}`}
              >
                {!notif.read && <span className="notification-item__dot" aria-hidden="true" />}
                <div className="notification-item__body">
                  <p className="notification-item__message">{notif.message}</p>
                  <span className="notification-item__time">{formatTime(notif.created_at)}</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </>
  )
}
