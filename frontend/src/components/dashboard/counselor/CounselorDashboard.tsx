import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { counselorApi } from '../../../api/counselor'
import { dashboardApi } from '../../../api/dashboard'
import { greeting } from '../../../lib/greeting'
import { useAuthStore } from '../../../store/authStore'
import Avatar from '../../common/Avatar'
import ActionCard from '../../common/dashboard/ActionCard'
import DashboardHero from '../../common/dashboard/DashboardHero'
import EmptyState from '../../common/dashboard/EmptyState'
import ErrorState from '../../common/dashboard/ErrorState'
import LoadingSkeleton from '../../common/dashboard/LoadingSkeleton'
import MetricCard from '../../common/dashboard/MetricCard'
import SectionHeader from '../../common/dashboard/SectionHeader'
import StatusBadge from '../../common/dashboard/StatusBadge'
import AssessmentRing from './AssessmentRing'
import '../../../styles/dashboard.css'

const REASON_PRIORITY = {
  learner_requested_review: 0,
  follow_up_overdue: 1,
  combination_unavailable_at_school: 2,
  academic_evidence_missing: 3,
  assessment_missing: 4,
  no_saved_combination: 5,
  no_plan: 6,
}

export default function CounselorDashboard() {
  const { user } = useAuthStore()
  const studentsQ = useQuery({
    queryKey: ['counselor', 'students'],
    queryFn: () => dashboardApi.getCounselorStudents().then((response) => response.data.data),
  })
  const statsQ = useQuery({
    queryKey: ['counselor', 'stats'],
    queryFn: () => dashboardApi.getCounselorStats().then((response) => response.data.data),
  })
  const interventionsQ = useQuery({
    queryKey: ['counselor', 'interventions'],
    queryFn: () => counselorApi.getInterventions().then((response) => response.data.data),
  })

  if (studentsQ.isLoading || statsQ.isLoading || interventionsQ.isLoading) {
    return <LoadingSkeleton label="Loading counsellor dashboard" rows={5} variant="metrics" />
  }

  if (studentsQ.isError || statsQ.isError || interventionsQ.isError) {
    return (
      <ErrorState
        title="The counsellor dashboard could not load"
        description="Check your connection and try loading the priority queue again."
        onRetry={() => {
          studentsQ.refetch()
          statsQ.refetch()
          interventionsQ.refetch()
        }}
      />
    )
  }

  const students = studentsQ.data ?? []
  const stats = statsQ.data ?? {
    total_students: 0,
    assessments_done: 0,
    students_needing_attention: 0,
    follow_ups_due: 0,
    journeys_reviewed: 0,
    notes_written: 0,
  }
  const priorityStudents = students
    .filter((student) => student.needs_attention)
    .sort((left, right) => {
      const leftPriority = Math.min(
        ...left.attention_reasons.map((reason) => REASON_PRIORITY[reason.code]),
      )
      const rightPriority = Math.min(
        ...right.attention_reasons.map((reason) => REASON_PRIORITY[reason.code]),
      )
      return leftPriority - rightPriority
    })
  const recentInterventions = [...(interventionsQ.data ?? [])]
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
    .slice(0, 4)
  const fullName = user ? `${user.first_name} ${user.last_name}`.trim() : 'Counsellor'

  return (
    <div className="db-page">
      <DashboardHero
        tone="counsellor"
        eyebrow="Counsellor workspace"
        title={user ? greeting(user.first_name) : 'Welcome'}
        description={stats.students_needing_attention > 0
          ? `${stats.students_needing_attention} learner${stats.students_needing_attention === 1 ? '' : 's'} have a clear reason for attention.`
          : 'Your assigned learners are up to date.'}
        avatar={<Avatar seed={fullName} size={46} shape="squircle" />}
        meta={[
          user?.county ? `${user.county} County` : '',
          `${stats.total_students} learner${stats.total_students === 1 ? '' : 's'} assigned`,
        ]}
        actions={[
          { label: 'Open full caseload', to: '/counselor/students' },
          { label: 'Manage interventions', to: '/counselor/students', variant: 'secondary' },
        ]}
      />

      <div className="db-metric-grid">
        <MetricCard
          label="Total students"
          value={stats.total_students}
          detail="Assigned to you"
          to="/counselor/students"
        />
        <MetricCard
          label="Need attention"
          value={stats.students_needing_attention}
          detail="With explicit reasons"
          tone={stats.students_needing_attention > 0 ? 'warning' : 'neutral'}
          to="/counselor/students"
        />
        <MetricCard
          label="Follow-ups due"
          value={stats.follow_ups_due}
          detail="Open actions due now"
          tone={stats.follow_ups_due > 0 ? 'warning' : 'positive'}
          to="/counselor/students"
        />
        <MetricCard
          label="Journeys reviewed"
          value={stats.journeys_reviewed}
          detail={`of ${stats.total_students} learner plans`}
          tone="positive"
        />
      </div>

      <section className="counselor-priority-grid" aria-label="Counsellor priority workflow">
        <div className="db-panel db-panel--compact">
          <SectionHeader
            eyebrow="Act next"
            title="Priority queue"
            description="Reasons are evidence gaps or agreed follow-ups, not a predictive risk score."
            action={{ label: 'View all learners', to: '/counselor/students' }}
          />
          {priorityStudents.length === 0 ? (
            <EmptyState
              title="No learners need attention"
              description="New evidence gaps and due follow-ups will appear here."
            />
          ) : (
            <div className="counselor-priority-list">
              {priorityStudents.slice(0, 5).map((student) => (
                <Link
                  key={student.id}
                  to={`/counselor/students/${student.id}`}
                  className="counselor-priority-card"
                >
                  <span>
                    <strong>{student.first_name} {student.last_name}</strong>
                    <small>Grade {student.grade}</small>
                  </span>
                  <span className="counselor-reason-list">
                    {student.attention_reasons.slice(0, 3).map((reason) => (
                      <span className="counselor-reason-chip" key={reason.code}>
                        {reason.label}
                      </span>
                    ))}
                  </span>
                  <span aria-hidden="true">→</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        <aside className="db-panel db-panel--compact db-stack">
          <SectionHeader eyebrow="Shortcuts" title="Direct actions" titleAs="h3" />
          <ActionCard
            title="Open full caseload"
            description="Filter learners and review all attention reasons."
            to="/counselor/students"
          />
          <ActionCard
            title="Manage interventions"
            description="Choose a learner and record an agreed next step."
            to="/counselor/students"
            tone="attention"
          />
          <ActionCard
            title="Review private notes"
            description="Keep confidential case notes separate from shared actions."
            to="/counselor/notes"
          />
        </aside>
      </section>

      <section className="db-content-grid" aria-label="Interventions and assessment coverage">
        <div className="db-panel db-panel--compact">
          <SectionHeader
            eyebrow="Activity"
            title="Recent interventions"
            action={{ label: 'Open caseload', to: '/counselor/students' }}
          />
          {recentInterventions.length === 0 ? (
            <EmptyState
              title="No interventions yet"
              description="Record an agreed action from a learner detail page."
              action={{ label: 'Choose a learner', to: '/counselor/students' }}
            />
          ) : (
            <div className="counselor-intervention-list">
              {recentInterventions.map((intervention) => (
                <article key={intervention.id} className="counselor-intervention">
                  <div>
                    <strong>{intervention.student_name}</strong>
                    <p>{intervention.action_agreed}</p>
                    <small>
                      {intervention.follow_up_date
                        ? `Follow up ${new Date(`${intervention.follow_up_date}T00:00:00`).toLocaleDateString('en-KE', {
                          day: 'numeric',
                          month: 'short',
                        })}`
                        : 'No follow-up date'}
                    </small>
                  </div>
                  <StatusBadge tone={intervention.status === 'completed' ? 'positive' : 'warning'}>
                    {intervention.status === 'completed' ? 'Completed' : 'Open'}
                  </StatusBadge>
                </article>
              ))}
            </div>
          )}
        </div>

        <aside className="db-panel db-panel--compact">
          <SectionHeader eyebrow="Coverage" title="Assessment progress" titleAs="h3" />
          <AssessmentRing done={stats.assessments_done} total={stats.total_students} />
        </aside>
      </section>
    </div>
  )
}
