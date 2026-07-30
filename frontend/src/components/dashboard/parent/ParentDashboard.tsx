import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../../store/authStore'
import { dashboardApi } from '../../../api/dashboard'
import { greeting } from '../../../lib/greeting'
import { useDownloadReport } from '../../../hooks/useDownloadReport'
import ChildHeader from './ChildHeader'
import Avatar from '../../common/Avatar'
import ActionCard from '../../common/dashboard/ActionCard'
import DashboardHero from '../../common/dashboard/DashboardHero'
import EmptyState from '../../common/dashboard/EmptyState'
import ErrorState from '../../common/dashboard/ErrorState'
import LoadingSkeleton from '../../common/dashboard/LoadingSkeleton'
import SectionHeader from '../../common/dashboard/SectionHeader'
import StatusBadge from '../../common/dashboard/StatusBadge'
import '../../../styles/dashboard.css'
import '../../../styles/parent-dashboard.css'

const PLAN_STATUS = {
  not_started: 'Not started',
  draft: 'Draft',
  ready_for_review: 'Ready for review',
  reviewed: 'Reviewed',
}

export default function ParentDashboard() {
  const { user } = useAuthStore()
  const { downloadReport, downloadingId } = useDownloadReport()
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null)

  const childrenQ = useQuery({
    queryKey: ['parent-children'],
    queryFn: () => dashboardApi.getParentChildren().then((response) => response.data.data),
  })
  const children = childrenQ.data ?? []

  useEffect(() => {
    if (childrenQ.isError) {
      toast.error("Couldn't load your children's data. Please try again.")
    }
  }, [childrenQ.isError])

  useEffect(() => {
    if (children.length && !children.some((child) => child.id === selectedChildId)) {
      setSelectedChildId(children[0].id)
    }
  }, [children, selectedChildId])

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
  const child = children.find((item) => item.id === selectedChildId) ?? children[0]

  return (
    <div className="db-page parent-support">
      <DashboardHero
        tone="parent"
        eyebrow="Parent workspace"
        title={user ? greeting(user.first_name) : 'Welcome'}
        description="Support the learner's next step with questions, encouragement and learner-approved information."
        avatar={<Avatar seed={fullName} size={46} shape="squircle" />}
        meta={[
          user?.county ? `${user.county} County` : '',
          `${children.length} approved learner${children.length === 1 ? '' : 's'}`,
        ]}
      />

      {child ? (
        <>
          <section aria-labelledby="parent-child-title">
            <SectionHeader
              eyebrow="Family view"
              title="Learner support"
              titleId="parent-child-title"
              description="Choose a learner to see the one action that matters now."
              aside={children.length > 1 ? (
                <label className="parent-switcher">
                  <span>Choose learner</span>
                  <select
                    value={child.id}
                    onChange={(event) => setSelectedChildId(Number(event.target.value))}
                  >
                    {children.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.first_name} {item.last_name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : undefined}
            />
          </section>

          <article className="db-panel parent-support__workspace">
            <ChildHeader child={child} />

            <div className="parent-support__action">
              <ActionCard
                title={child.next_action.title}
                description={`Open ${child.first_name}'s learner-approved summary and support this next step.`}
                to={`/parent/child/${child.id}`}
                tone="attention"
                status={<StatusBadge tone="attention">Next action</StatusBadge>}
              />
            </div>

            <div className="parent-support__grid">
              <section className="parent-support__card">
                <span>Provisional direction</span>
                {child.provisional_combination ? (
                  <>
                    <h3>{child.provisional_combination.title}</h3>
                    <p>
                      {child.provisional_combination.pathway} · {child.provisional_combination.track}
                    </p>
                    <small>{child.provisional_combination.code}</small>
                  </>
                ) : (
                  <>
                    <h3>No provisional combination yet</h3>
                    <p>Encourage comparison without choosing on the learner's behalf.</p>
                  </>
                )}
              </section>

              <section className="parent-support__card">
                <span>Plan progress</span>
                <div className="parent-support__status-row">
                  <h3>{PLAN_STATUS[child.plan_status]}</h3>
                  <StatusBadge tone={child.plan_status === 'reviewed' ? 'positive' : 'neutral'}>
                    {child.plan_progress.completed} of {child.plan_progress.total} milestones
                  </StatusBadge>
                </div>
                {child.upcoming_milestone ? (
                  <p>
                    Next: <strong>{child.upcoming_milestone.title}</strong>
                    {child.upcoming_milestone.due_date
                      ? ` · due ${formatDate(child.upcoming_milestone.due_date)}`
                      : ''}
                  </p>
                ) : (
                  <p>No upcoming milestone has been recorded.</p>
                )}
              </section>

              <section className="parent-support__card parent-support__card--prompt">
                <span>Conversation prompt</span>
                <h3>Ask, then listen</h3>
                <blockquote>“{child.conversation_prompt}”</blockquote>
              </section>

              <section className="parent-support__card">
                <span>Access and report</span>
                <div className="parent-support__status-row">
                  <h3>Learner approved</h3>
                  <StatusBadge tone="positive">Active access</StatusBadge>
                </div>
                <p>You can view only information approved for parent access.</p>
                <div className="parent-support__buttons">
                  <Link to={`/parent/child/${child.id}`}>View learner summary</Link>
                  <button
                    type="button"
                    disabled={downloadingId === child.id}
                    onClick={() => downloadReport(child.id)}
                  >
                    {downloadingId === child.id ? 'Preparing report...' : 'Download report'}
                  </button>
                </div>
              </section>
            </div>
          </article>
        </>
      ) : (
        <EmptyState
          title="No learner access approved yet"
          description="A learner you were invited to support must approve access before their information appears here."
        />
      )}
    </div>
  )
}

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
