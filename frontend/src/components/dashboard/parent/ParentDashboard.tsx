import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../../store/authStore'
import { dashboardApi } from '../../../api/dashboard'
import ChildHeader from './ChildHeader'
import '../../../styles/dashboard.css'

function greeting(name: string) {
  const h = new Date().getHours()
  if (h < 12) return `Good morning, ${name}`
  if (h < 17) return `Good afternoon, ${name}`
  return `Good evening, ${name}`
}

export default function ParentDashboard() {
  const { user } = useAuthStore()

  const childrenQ = useQuery({
    queryKey: ['parent-children'],
    queryFn: () => dashboardApi.getParentChildren().then((r) => r.data.data),
  })

  const children = childrenQ.data ?? []
  const child = children[0] ?? null

  return (
    <div>
      <div className="greeting-strip" style={{ marginBottom: 'var(--space-5)' }} role="region" aria-label="Welcome banner">
        <div className="greeting-strip__avatar" aria-hidden="true">
          {user ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase() : '?'}
        </div>
        <div className="greeting-strip__body">
          <div className="greeting-strip__hello">{user ? greeting(user.first_name) : ''}</div>
          <div className="greeting-strip__name">{user?.first_name} {user?.last_name}</div>
          <div className="greeting-strip__chips">
            <span className="greeting-chip">Parent</span>
            {user?.county && <span className="greeting-chip" style={{ textTransform: 'capitalize' }}>{user.county}</span>}
          </div>
        </div>
      </div>

      {child ? (
        <>
          <ChildHeader child={child} />

          <div className="dashboard-grid">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
              <div className="dashboard-card">
                <p className="dashboard-card__title">{child.first_name}'s career personality</p>
                {child.top_pathway ? (
                  <div style={{ padding: 'var(--space-4)', background: 'var(--color-primary-surface)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{child.top_pathway}</div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                      Top career pathway · {child.fit_pct}% fit
                    </div>
                  </div>
                ) : (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                    Career quiz not completed yet.
                  </p>
                )}
              </div>

              <div className="dashboard-card">
                <p className="dashboard-card__title">{child.first_name}'s recent grades</p>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                  {child.subject_count > 0
                    ? `${child.subject_count} subject${child.subject_count !== 1 ? 's' : ''} enrolled.`
                    : 'No subjects added yet.'}
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
              <div className="counselor-card">
                <p className="dashboard-card__title" style={{ marginBottom: 'var(--space-3)' }}>Counselor's note</p>
                {child.counselor_assigned ? (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', fontStyle: 'italic' }}>
                    No notes yet from the counselor.
                  </p>
                ) : (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                    No counselor assigned yet.
                  </p>
                )}
              </div>

              <div className="dashboard-card">
                <p className="dashboard-card__title">Recent updates</p>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                  No recent activity for {child.first_name}.
                </p>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="dashboard-card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
            No child linked to your account yet.
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Parent–student links are set up in Sprint 7.
          </p>
        </div>
      )}
    </div>
  )
}
