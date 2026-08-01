import { useQuery } from '@tanstack/react-query'
import { schoolAdminApi } from '../../../api/schoolAdmin'
import ActionCard from '../../common/dashboard/ActionCard'
import DashboardHero from '../../common/dashboard/DashboardHero'
import ErrorState from '../../common/dashboard/ErrorState'
import MetricCard from '../../common/dashboard/MetricCard'
import SectionHeader from '../../common/dashboard/SectionHeader'
import StatusBadge from '../../common/dashboard/StatusBadge'
import '../../../styles/dashboard.css'
import '../../../styles/school-admin.css'

export default function SchoolAdminDashboard() {
  const schoolQ = useQuery({
    queryKey: ['school-admin', 'school'],
    queryFn: () => schoolAdminApi.getSchool().then(r => r.data.data),
  })

  const statsQ = useQuery({
    queryKey: ['school-admin', 'stats'],
    queryFn: () => schoolAdminApi.getStats().then(r => r.data.data),
  })

  if (schoolQ.isLoading || statsQ.isLoading) {
    return (
      <div className="school-admin-dashboard">
        <div className="skeleton" style={{ height: 180, borderRadius: 'var(--radius-xl)', marginBottom: 'var(--space-5)' }} />
        <div className="dashboard-stats-grid">
          {[1, 2, 3, 4].map((item) => (
            <div key={item} className="skeleton-card">
              <div className="skeleton" style={{ height: 16, width: '40%' }} />
              <div className="skeleton" style={{ height: 40 }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (schoolQ.isError || statsQ.isError) {
    return (
      <ErrorState
        title="The school dashboard could not load"
        description="Check your connection and try loading the school summary again."
        onRetry={() => {
          schoolQ.refetch()
          statsQ.refetch()
        }}
      />
    )
  }

  const school = schoolQ.data
  const stats = statsQ.data

  return (
    <div className="db-page school-admin-dashboard school-operations">
      <DashboardHero
        tone="school"
        eyebrow="School operations"
        title={school?.name ?? 'School dashboard'}
        description="Approve learner access, balance counsellor workload and monitor the pilot journey."
        avatar={school?.logo_url ? (
          <img
            src={school.logo_url}
            alt={`${school.name} logo`}
            className="school-admin-dashboard__logo"
          />
        ) : undefined}
        meta={[
          school ? `${school.county} County` : '',
          school?.school_code ?? 'KNEC code not yet recorded',
          'Five-county pilot',
        ]}
        actions={[
          { label: 'Review students', to: '/admin/students' },
          { label: 'Manage counsellors', to: '/admin/counselors', variant: 'secondary' },
        ]}
      />

      <section aria-labelledby="school-overview-title">
        <SectionHeader
          eyebrow="Today"
          title="Operations overview"
          titleId="school-overview-title"
          description="Approval and assignment counts update from current learner records."
        />
        <div className="db-metrics-grid school-operations__overview">
          <MetricCard label="Students" value={stats?.total_students ?? 0} detail="Approved learners" to="/admin/students" tone="positive" />
          <MetricCard label="Pending school links" value={stats?.pending_memberships ?? 0} detail="Awaiting a decision" to="/admin/students" tone="warning" />
          <MetricCard label="Unassigned" value={stats?.unassigned ?? 0} detail="Approved learners" to="/admin/students" tone="attention" />
          <MetricCard label="Counselors" value={stats?.total_counselors ?? 0} detail="School team" to="/admin/counselors" tone="info" />
        </div>
      </section>

      <section aria-labelledby="school-journey-title">
        <SectionHeader
          eyebrow="Cohort progress"
          title="Learner journey"
          titleId="school-journey-title"
          description="Counts show completed evidence and journey stages for approved learners."
        />
        <div className="db-metrics-grid school-operations__journey">
          <MetricCard label="Evidence ready" value={stats?.evidence_complete ?? 0} detail="3+ subjects with grades" tone="positive" />
          <MetricCard label="Assessed" value={stats?.assessed ?? 0} detail="Interest assessment complete" tone="info" />
          <MetricCard label="Choices saved" value={stats?.choices_saved ?? 0} detail="At least one combination" tone="neutral" />
          <MetricCard label="Plans created" value={stats?.plans_created ?? 0} detail="Learner action plans" tone="warning" />
          <MetricCard label="Reviews completed" value={stats?.reviews_completed ?? 0} detail="Counsellor-reviewed plans" tone="positive" />
        </div>
      </section>

      <div className="school-operations__workspace">
        <section className="db-panel db-panel--compact" aria-labelledby="school-workload-title">
          <SectionHeader
            eyebrow="Assignments"
            title="Counsellor workload"
            titleId="school-workload-title"
            action={{ label: 'Manage counsellors', to: '/admin/counselors' }}
          />
          {stats?.counselor_workload.length ? (
            <ul className="school-workload">
              {stats.counselor_workload.map(counselor => (
                <li key={counselor.counselor_id}>
                  <span>{counselor.counselor_name}</span>
                  <strong>
                    {counselor.student_count} learner{counselor.student_count === 1 ? '' : 's'}
                  </strong>
                </li>
              ))}
            </ul>
          ) : (
            <p className="school-operations__empty">No counsellors have joined this school yet.</p>
          )}
        </section>

        <section className="db-panel db-panel--compact" aria-labelledby="school-offerings-title">
          <SectionHeader
            eyebrow="Curriculum readiness"
            title="School offerings"
            titleId="school-offerings-title"
            action={{ label: 'Configure offerings', to: '/admin/offerings' }}
          />
          <div className="school-offerings-status">
            <StatusBadge tone={stats?.offerings_configured ? 'positive' : 'warning'}>
              {stats?.offerings_configured ? 'Offerings configured' : 'Configuration needed'}
            </StatusBadge>
            <strong>{stats?.offerings_count ?? 0} active combinations</strong>
            <p>
              Learners can compare provisional choices with combinations available at this school.
            </p>
          </div>
        </section>
      </div>

      <section aria-labelledby="school-actions-title">
        <SectionHeader eyebrow="Administration" title="Quick actions" titleId="school-actions-title" />
        <div className="school-operations__actions">
          <ActionCard
            title="Manage School Profile"
            description="Update school contact details and logo."
            to="/admin/school"
            tone="neutral"
          />
          <ActionCard
            title="Manage Counselors"
            description="Add counsellors and review their assigned learners."
            to="/admin/counselors"
            tone="info"
          />
          <ActionCard
            title="Review learner access"
            description="Approve pending school links and assign approved learners."
            to="/admin/students"
            tone="warning"
          />
        </div>
      </section>
    </div>
  )
}
