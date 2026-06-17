import type { CounselorInfo } from '../../../api/dashboard'
import { useNotificationStore } from '../../../store/notificationStore'

interface Props {
  counselor: CounselorInfo | null
}

function initials(c: CounselorInfo) {
  return `${c.first_name[0] ?? ''}${c.last_name[0] ?? ''}`.toUpperCase()
}

export default function CounselorCard({ counselor }: Props) {
  const { setDrawerOpen } = useNotificationStore()

  return (
    <div className="counselor-card">
      {counselor ? (
        <>
          <div className="counselor-card__header">
            <div className="counselor-card__avatar" aria-hidden="true">{initials(counselor)}</div>
            <div className="counselor-card__meta">
              <div className="counselor-card__name">{counselor.first_name} {counselor.last_name}</div>
              <div className="counselor-card__role">Career Counselor</div>
            </div>
          </div>
          {counselor.last_message ? (
            <blockquote className="counselor-card__message">
              "{counselor.last_message}"
            </blockquote>
          ) : (
            <p className="counselor-card__message" style={{ fontStyle: 'normal', color: 'var(--color-text-secondary)' }}>
              No messages yet from your counselor.
            </p>
          )}
          <button
            className="btn-primary"
            onClick={() => setDrawerOpen(true)}
            style={{ width: '100%' }}
          >
            Message counselor
          </button>
        </>
      ) : (
        <div className="counselor-card__empty">
          <p style={{ marginBottom: 'var(--space-2)' }}>No counselor assigned yet.</p>
          <p style={{ fontSize: 'var(--font-size-xs)' }}>
            Counselors are assigned to school-linked accounts. Switch to school mode in your profile settings.
          </p>
        </div>
      )}
    </div>
  )
}
