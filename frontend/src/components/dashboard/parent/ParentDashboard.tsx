import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../../store/authStore'
import { dashboardApi, LinkedChild } from '../../../api/dashboard'
import { greeting } from '../../../lib/greeting'
import ChildHeader from './ChildHeader'
import Avatar from '../../common/Avatar'
import DashboardHero from '../../common/dashboard/DashboardHero'
import EmptyState from '../../common/dashboard/EmptyState'
import ErrorState from '../../common/dashboard/ErrorState'
import LoadingSkeleton from '../../common/dashboard/LoadingSkeleton'
import SectionHeader from '../../common/dashboard/SectionHeader'
import StatusBadge from '../../common/dashboard/StatusBadge'
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
    return <LoadingSkeleton label="Loading parent dashboard" rows={3} />
  }

  if (childrenQ.isError) {
    return (
      <ErrorState
        title="Your children's information could not load"
        description="Check your connection and try again."
        onRetry={() => childrenQ.refetch()}
      />
    )
  }

  const fullName = user ? `${user.first_name} ${user.last_name}`.trim() : 'Parent'

  return (
    <div className="db-page">
      <DashboardHero
        tone="parent"
        eyebrow="Parent workspace"
        title={user ? greeting(user.first_name) : 'Welcome'}
        description="Follow each learner's interests, subjects, and guidance conversations in one place."
        avatar={<Avatar seed={fullName} size={46} shape="squircle" />}
        meta={[
          user?.county ? `${user.county} County` : '',
          `${children.length} child${children.length === 1 ? '' : 'ren'} linked`,
        ]}
      />

      {children.length > 0 ? (
        <section className="db-stack" aria-labelledby="parent-children-title">
          <SectionHeader
            eyebrow="Family view"
            title="Your children"
            titleId="parent-children-title"
            description="Open a learner profile to review their evidence and latest guidance."
          />
          {children.map((child: LinkedChild) => (
            <article key={child.id} className="db-panel">
              <ChildHeader child={child} />
              <div className="db-panel__grid">
                <div className="db-panel__section">
                  <h3>{child.first_name}'s interest profile</h3>
                  {child.top_pathway ? (
                    <div className="db-panel__highlight">
                      <strong>{child.top_pathway}</strong>
                      <StatusBadge tone="positive">Strongest interest alignment</StatusBadge>
                    </div>
                  ) : (
                    <p className="db-panel__muted">Career quiz not completed yet.</p>
                  )}
                </div>
                <div className="db-panel__section">
                  <h3>{child.first_name}'s subjects</h3>
                  <p className="db-panel__muted">
                    {child.subject_count > 0
                      ? `${child.subject_count} subject${child.subject_count !== 1 ? 's' : ''} enrolled.`
                      : 'No subjects added yet.'}
                  </p>
                </div>
              </div>
              <footer className="db-panel__footer">
                <Link
                  to={`/parent/child/${child.id}`}
                  className="db-panel__link"
                  aria-label={`View profile for ${child.first_name}`}
                >
                  View learner profile <span aria-hidden="true">→</span>
                </Link>
              </footer>
            </article>
          ))}
        </section>
      ) : (
        <EmptyState
          title="No child linked yet"
          description="Contact your school to link a learner account to this parent workspace."
        />
      )}
    </div>
  )
}
