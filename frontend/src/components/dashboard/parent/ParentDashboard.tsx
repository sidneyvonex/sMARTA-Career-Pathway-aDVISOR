import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../../store/authStore'
import { dashboardApi, LinkedChild } from '../../../api/dashboard'
import { greeting } from '../../../lib/greeting'
import { initials } from '../../../lib/format'
import ChildHeader from './ChildHeader'
import '../../../styles/dashboard.css'

export default function ParentDashboard() {
  const { user } = useAuthStore()

  const childrenQ = useQuery({
    queryKey: ['parent-children'],
    queryFn: () => dashboardApi.getParentChildren().then((r) => r.data.data),
  })

  const children = childrenQ.data ?? []

  useEffect(() => {
    if (childrenQ.isError) {
      toast.error("Couldn't load your children's data. Please try again.")
    }
  }, [childrenQ.isError])

  if (childrenQ.isLoading) {
    return (
      <div>
        <div className="skeleton" style={{ height: 140, borderRadius: 13, marginBottom: 'var(--space-5)' }} />
        <div className="skeleton" style={{ height: 200, borderRadius: 13 }} />
      </div>
    )
  }

  if (childrenQ.isError) {
    return (
      <div className="dashboard-card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Couldn't load your children's data. Please try again.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="greeting-strip" style={{ marginBottom: 'var(--space-5)' }} role="region" aria-label="Welcome banner">
        <div className="greeting-strip__avatar" aria-hidden="true">
          {user ? initials(user.first_name, user.last_name) : '?'}
        </div>
        <div className="greeting-strip__body">
          <div className="greeting-strip__hello">{user ? greeting(user.first_name) : ''}</div>
          <div className="greeting-strip__name">{user?.first_name} {user?.last_name}</div>
          <div className="greeting-strip__chips">
            <span className="greeting-chip">Parent</span>
            {user?.county && <span className="greeting-chip" style={{ textTransform: 'capitalize' }}>{user.county}</span>}
            <span className="greeting-chip">{children.length} child{children.length !== 1 ? 'ren' : ''}</span>
          </div>
        </div>
      </div>

      {children.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
          {children.map((child: LinkedChild) => (
            <div key={child.id} className="dashboard-card" style={{ padding: 0, overflow: 'hidden' }}>
              <ChildHeader child={child} />
              <div style={{ padding: 'var(--space-4)', display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <p className="dashboard-card__title">{child.first_name}'s career personality</p>
                  {child.top_pathway ? (
                    <div style={{ padding: 'var(--space-3)', background: 'var(--color-primary-surface)', borderRadius: 'var(--radius-md)' }}>
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
                <div style={{ flex: 1, minWidth: 200 }}>
                  <p className="dashboard-card__title">{child.first_name}'s subjects</p>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                    {child.subject_count > 0
                      ? `${child.subject_count} subject${child.subject_count !== 1 ? 's' : ''} enrolled.`
                      : 'No subjects added yet.'}
                  </p>
                </div>
              </div>
              <div style={{ padding: '0 var(--space-4) var(--space-4)' }}>
                <Link
                  to={`/parent/child/${child.id}`}
                  className="btn-ghost"
                  style={{ fontSize: 'var(--font-size-sm)' }}
                  aria-label={`View profile for ${child.first_name}`}
                >
                  View profile
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="dashboard-card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
            No child linked to your account yet.
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Contact your school to link your child's account.
          </p>
        </div>
      )}
    </div>
  )
}
