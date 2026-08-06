import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { systemAdminApi } from '../../api/systemAdmin'
import { reportsApi } from '../../api/reports'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import ActionCard from '../common/dashboard/ActionCard'
import ActivityList from '../common/dashboard/ActivityList'
import DashboardHero from '../common/dashboard/DashboardHero'
import EmptyState from '../common/dashboard/EmptyState'
import ErrorState from '../common/dashboard/ErrorState'
import MetricCard from '../common/dashboard/MetricCard'
import SectionHeader from '../common/dashboard/SectionHeader'
import { formatDate } from '../../lib/format'
import '../../styles/dashboard.css'
import '../../styles/system-admin.css'

const ACTION_LABELS: Record<string, string> = {
  user_registered: 'User registered',
  email_verified: 'Email verified',
  password_reset: 'Password reset',
  account_deactivated: 'Account deactivated',
  account_activated: 'Account activated',
  invite_sent: 'Invite sent',
  invite_accepted: 'Invite accepted',
  school_created: 'School created',
  school_edited: 'School edited',
  school_deactivated: 'School deactivated',
  school_activated: 'School activated',
  counselor_added: 'Counsellor added',
  counselor_removed: 'Counsellor removed',
  counselor_assigned: 'Counsellor assigned',
  school_membership_approved: 'School link approved',
  school_membership_rejected: 'School link rejected',
  grade_verified: 'Grade verified',
  school_marks_imported: 'School marks imported',
  grade_verification_removed: 'Grade verification removed',
  parent_link_approved: 'Parent link approved',
  parent_link_revoked: 'Parent link revoked',
  provisional_combination_changed: 'Provisional combination changed',
  plan_review_status_changed: 'Plan review status changed',
  report_downloaded: 'Report downloaded',
  framework_combination_status_changed: 'Framework combination status changed',
  school_offerings_changed: 'School offerings changed',
}

const COUNTY_LABELS: Record<string, string> = {
  kiambu: 'Kiambu',
  muranga: "Murang'a",
  nyeri: 'Nyeri',
  kirinyaga: 'Kirinyaga',
  nyandarua: 'Nyandarua',
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  const minutes = Math.floor((Date.now() - date.getTime()) / 60000)
  if (minutes < 60) return `${Math.max(minutes, 0)}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return formatDate(iso)
}

export default function SystemAdminDashboard() {
  const { downloadReport, downloadingKey } = useDownloadReport()
  const dashboardQ = useQuery({
    queryKey: ['system-admin', 'dashboard'],
    queryFn: () => systemAdminApi.getDashboard().then(response => response.data.data),
  })

  if (dashboardQ.isLoading) {
    return (
      <div className="sysadmin-dashboard">
        <div className="skeleton" style={{ height: 180, borderRadius: 'var(--radius-xl)', marginBottom: 'var(--space-5)' }} />
        <div className="dashboard-stats-grid">
          {[1, 2, 3, 4].map(item => <div key={item} className="skeleton-card" />)}
        </div>
      </div>
    )
  }

  if (dashboardQ.isError || !dashboardQ.data) {
    return (
      <ErrorState
        title="The pilot dashboard could not load"
        description="No administration data was changed. Check your connection and try again."
        onRetry={() => dashboardQ.refetch()}
        actionLabel="Retry dashboard"
      />
    )
  }

  const stats = dashboardQ.data
  const roles = stats.users_by_role

  return (
    <div className="db-page sysadmin-dashboard pilot-admin">
      <DashboardHero
        tone="system"
        eyebrow="System administration"
        title="System Admin Dashboard"
        description="Monitor the five-county project rollout, current guidance framework and important operational events."
        meta={[
          `${stats.total_schools} active schools`,
          `${stats.registered_learners} registered learners`,
          'Five rollout counties',
        ]}
        actions={[
          { label: 'Create School', to: '/system-admin/schools?create=1' },
          { label: 'Manage Catalogue', to: '/system-admin/catalogue', variant: 'secondary' },
          { label: 'View Audit Log', to: '/system-admin/audit-log', variant: 'secondary' },
        ]}
      />

      <section aria-labelledby="pilot-health-title">
        <SectionHeader
          eyebrow="Pilot health"
          title="Access and completion"
          titleId="pilot-health-title"
          description="Counts use live learner verification, school-link, assignment and reviewed-plan records."
        />
        <div className="db-metrics-grid pilot-admin__health">
          <MetricCard label="Learners" value={roles.student ?? 0} detail="User accounts" to="/system-admin/users?role=student" tone="neutral" />
          <MetricCard label="Verified learners" value={stats.verified_learners} detail={`${stats.registered_learners} registered`} to="/system-admin/users?role=student" tone="positive" />
          <MetricCard label="Pending school links" value={stats.pending_school_links} detail="Awaiting school decision" tone="warning" />
          <MetricCard label="Assignment coverage" value={`${stats.assignment_coverage.percent}%`} detail={`${stats.assignment_coverage.assigned} of ${stats.assignment_coverage.eligible}`} tone="info" />
          <MetricCard label="Plans completed" value={stats.plans_completed} detail="Counsellor reviewed" tone="positive" />
          <MetricCard label="Schools" value={stats.total_schools} detail="Active rollout schools" to="/system-admin/schools" tone="info" />
          <MetricCard label="Counsellors" value={roles.counselor ?? 0} detail="Across rollout schools" to="/system-admin/users?role=counselor" tone="neutral" />
          <MetricCard label="Parents" value={roles.parent ?? 0} detail="Supporter accounts" to="/system-admin/users?role=parent" tone="neutral" />
        </div>
      </section>

      <section aria-labelledby="county-title">
        <SectionHeader
          eyebrow="Pilot footprint"
          title="Schools by County"
          titleId="county-title"
          description="This project currently limits registration and school discovery to five rollout counties."
        />
        <div className="pilot-admin__counties">
          {Object.entries(COUNTY_LABELS).map(([county, label]) => (
            <article className="pilot-county-card" key={county}>
              <strong>{label}</strong>
              <span>{stats.learners_by_county[county] ?? 0} learners</span>
              <span>{stats.schools_by_county[county] ?? 0} schools</span>
            </article>
          ))}
        </div>
      </section>

      <div className="pilot-admin__workspace">
        <section className="db-panel db-panel--compact" aria-labelledby="framework-title">
          <SectionHeader
            eyebrow="Catalogue freshness"
            title="Current guidance framework"
            titleId="framework-title"
          />
          {stats.framework ? (
            <div className="pilot-framework">
              <strong>{stats.framework.code}</strong>
              <h3>{stats.framework.title}</h3>
              <p>Effective {formatDate(stats.framework.effective_date)}</p>
              <a href={stats.framework.source_url} target="_blank" rel="noreferrer">
                Open official source
              </a>
              <Link to="/system-admin/catalogue">
                Manage catalogue status
              </Link>
            </div>
          ) : (
            <EmptyState
              title="No active framework"
              description="Activate a source-dated guidance framework before the presentation."
            />
          )}
        </section>

        <section className="db-panel db-panel--compact" aria-labelledby="recent-activity-title">
          <SectionHeader
            eyebrow="Important events"
            title="Recent activity"
            titleId="recent-activity-title"
            action={{ label: 'View all', to: '/system-admin/audit-log' }}
          />
          <ActivityList
            items={stats.recent_audit.map(entry => ({
              id: entry.id,
              title: ACTION_LABELS[entry.action] ?? entry.action.replace(/_/g, ' '),
              detail: entry.actor_name || entry.actor_email || 'System',
              time: formatTime(entry.created_at),
            }))}
            ariaLabel="Recent important audit events"
            empty={<EmptyState title="No recent activity" description="Important rollout actions will appear here." />}
          />
        </section>
      </div>

      <section aria-labelledby="platform-reports-title">
        <SectionHeader
          eyebrow="Exports"
          title="Platform reports"
          titleId="platform-reports-title"
          description="Download rollout metrics or the registered schools directory."
        />
        <div className="report-download-controls report-download-controls--two">
          <ActionCard
            title={downloadingKey === 'platform-overview' ? 'Generating overview…' : 'Download platform overview'}
            description="User, verification, assignment and completion metrics."
            onClick={() => downloadReport(
              reportsApi.downloadPlatformOverviewPdf,
              'smarta-shauri-platform-overview.pdf',
              'platform-overview',
            )}
            disabled={downloadingKey !== null}
            tone="info"
          />
          <ActionCard
            title={downloadingKey === 'schools-directory' ? 'Generating directory…' : 'Download schools directory'}
            description="School status and learner/counsellor totals."
            onClick={() => downloadReport(
              reportsApi.downloadSchoolsDirectoryPdf,
              'smarta-shauri-schools-directory.pdf',
              'schools-directory',
            )}
            disabled={downloadingKey !== null}
            tone="positive"
          />
        </div>
      </section>
    </div>
  )
}
