import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { systemAdminApi } from '../../api/systemAdmin'
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
  counselor_added: 'Counselor added',
  counselor_removed: 'Counselor removed',
  counselor_assigned: 'Counselor assigned',
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return d.toLocaleDateString()
}

export default function SystemAdminDashboard() {
  const navigate = useNavigate()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['system-admin', 'dashboard'],
    queryFn: () => systemAdminApi.getDashboard().then(r => r.data.data),
  })

  if (isLoading) {
    return (
      <div className="sysadmin-dashboard">
        <div className="skeleton" style={{ height: 40, width: '60%', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-5)' }} />
        <div className="dashboard-stats-grid">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton-card">
              <div className="skeleton" style={{ height: 16, width: '40%' }} />
              <div className="skeleton" style={{ height: 40 }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    toast.error('Failed to load dashboard data.')
    return (
      <div className="sysadmin-dashboard">
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          Something went wrong loading the dashboard. Please try again.
        </p>
      </div>
    )
  }

  const stats = data!
  const roles = stats.users_by_role
  const counties = stats.schools_by_county

  return (
    <div className="sysadmin-dashboard">
      <h1 className="sysadmin-dashboard__title">System Admin Dashboard</h1>
      <p className="sysadmin-dashboard__subtitle">Smarta Shauri platform overview</p>

      <div className="dashboard-stats-grid">
        <div className="dashboard-stat-card" onClick={() => navigate('/system-admin/users?role=student')}>
          <span className="dashboard-stat-card__value">{roles.student ?? 0}</span>
          <span className="dashboard-stat-card__label">Students</span>
        </div>
        <div className="dashboard-stat-card" onClick={() => navigate('/system-admin/users?role=counselor')}>
          <span className="dashboard-stat-card__value">{roles.counselor ?? 0}</span>
          <span className="dashboard-stat-card__label">Counselors</span>
        </div>
        <div className="dashboard-stat-card" onClick={() => navigate('/system-admin/schools')}>
          <span className="dashboard-stat-card__value">{stats.total_schools}</span>
          <span className="dashboard-stat-card__label">Schools</span>
        </div>
        <div className="dashboard-stat-card" onClick={() => navigate('/system-admin/users?role=parent')}>
          <span className="dashboard-stat-card__value">{roles.parent ?? 0}</span>
          <span className="dashboard-stat-card__label">Parents</span>
        </div>
      </div>

      <h2 className="sysadmin-section-title">Schools by County</h2>
      <div className="sysadmin-county-grid">
        {['kiambu', 'muranga', 'nyeri', 'kirinyaga', 'nyandarua'].map(c => (
          <div key={c} className="sysadmin-county-card">
            <div className="sysadmin-county-card__count">{counties[c] ?? 0}</div>
            <div className="sysadmin-county-card__name">{c === 'muranga' ? "Murang'a" : c}</div>
          </div>
        ))}
      </div>

      <h2 className="sysadmin-section-title">Recent Activity</h2>
      {stats.recent_audit.length === 0 ? (
        <p className="admin-empty-state">No recent activity.</p>
      ) : (
        <ul className="sysadmin-activity-list">
          {stats.recent_audit.map(entry => (
            <li key={entry.id} className="sysadmin-activity-item">
              <div>
                <span className="sysadmin-activity-item__action">
                  {ACTION_LABELS[entry.action] ?? entry.action}
                </span>
                {entry.actor_name && (
                  <span className="sysadmin-activity-item__actor"> — {entry.actor_name}</span>
                )}
              </div>
              <span className="sysadmin-activity-item__time">{formatTime(entry.created_at)}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="sysadmin-dashboard__actions">
        <button className="btn-primary" onClick={() => navigate('/system-admin/schools?create=1')}>
          Create School
        </button>
        <button className="btn-ghost" onClick={() => navigate('/system-admin/audit-log')}>
          View Audit Log
        </button>
      </div>
    </div>
  )
}
