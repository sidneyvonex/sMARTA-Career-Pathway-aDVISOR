import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { schoolAdminApi } from '../../../api/schoolAdmin'
import '../../../styles/school-admin.css'

export default function SchoolAdminDashboard() {
  const navigate = useNavigate()

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
        <div className="skeleton" style={{ height: 80, borderRadius: 13, marginBottom: 'var(--space-5)' }} />
        <div className="dashboard-stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton-card">
              <div className="skeleton" style={{ height: 16, width: '40%' }} />
              <div className="skeleton" style={{ height: 40 }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const school = schoolQ.data
  const stats = statsQ.data

  return (
    <div className="school-admin-dashboard">
      <div className="school-admin-dashboard__header">
        {school?.logo_url && (
          <img src={school.logo_url} alt={`${school.name} logo`} className="school-admin-dashboard__logo" />
        )}
        <div>
          <h1 className="school-admin-dashboard__title">{school?.name}</h1>
          <p className="school-admin-dashboard__subtitle">{school?.county} County · {school?.school_code}</p>
        </div>
      </div>

      <div className="dashboard-stats-grid">
        <button className="dashboard-stat-card" onClick={() => navigate('/admin/students')}>
          <span className="dashboard-stat-card__value">{stats?.total_students ?? 0}</span>
          <span className="dashboard-stat-card__label">Students</span>
        </button>
        <button className="dashboard-stat-card" onClick={() => navigate('/admin/counselors')}>
          <span className="dashboard-stat-card__value">{stats?.total_counselors ?? 0}</span>
          <span className="dashboard-stat-card__label">Counselors</span>
        </button>
        <button className="dashboard-stat-card dashboard-stat-card--success">
          <span className="dashboard-stat-card__value">{stats?.assessed ?? 0}</span>
          <span className="dashboard-stat-card__label">Assessed</span>
        </button>
        <button className="dashboard-stat-card dashboard-stat-card--warning" onClick={() => navigate('/admin/students')}>
          <span className="dashboard-stat-card__value">{stats?.unassigned ?? 0}</span>
          <span className="dashboard-stat-card__label">Unassigned</span>
        </button>
      </div>

      <div className="school-admin-dashboard__actions">
        <button className="btn-primary" onClick={() => navigate('/admin/school')}>
          Manage School Profile
        </button>
        <button className="btn-ghost" onClick={() => navigate('/admin/counselors')}>
          Manage Counselors
        </button>
      </div>
    </div>
  )
}
