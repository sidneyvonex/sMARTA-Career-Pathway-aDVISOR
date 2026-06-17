import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../../store/authStore'
import { dashboardApi } from '../../../api/dashboard'
import AssessmentRing from './AssessmentRing'
import StudentList from './StudentList'
import '../../../styles/dashboard.css'

function greeting(name: string) {
  const h = new Date().getHours()
  if (h < 12) return `Good morning, ${name}`
  if (h < 17) return `Good afternoon, ${name}`
  return `Good evening, ${name}`
}

export default function CounselorDashboard() {
  const { user } = useAuthStore()

  const studentsQ = useQuery({
    queryKey: ['counselor-students'],
    queryFn: () => dashboardApi.getCounselorStudents().then((r) => r.data.data),
  })

  const statsQ = useQuery({
    queryKey: ['counselor-stats'],
    queryFn: () => dashboardApi.getCounselorStats().then((r) => r.data.data),
  })

  const students = studentsQ.data ?? []
  const stats = statsQ.data ?? { total_students: 0, assessments_done: 0, students_needing_attention: 0, notes_written: 0 }

  return (
    <div>
      <div className="greeting-strip" role="region" aria-label="Welcome banner">
        <div className="greeting-strip__avatar" aria-hidden="true">
          {user ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase() : '?'}
        </div>
        <div className="greeting-strip__body">
          <div className="greeting-strip__hello">{user ? greeting(user.first_name) : ''}</div>
          <div className="greeting-strip__name">{user?.first_name} {user?.last_name}</div>
          <div className="greeting-strip__chips">
            <span className="greeting-chip">Career Counselor</span>
            {user?.county && <span className="greeting-chip" style={{ textTransform: 'capitalize' }}>{user.county}</span>}
            {stats.students_needing_attention > 0 && (
              <span className="greeting-chip greeting-chip--gold">
                {stats.students_needing_attention} students need attention
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-card__label">Total students</div>
          <div className="stat-card__value">{stats.total_students}</div>
          <div className="stat-card__sub">Assigned to you</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Assessments done</div>
          <div className="stat-card__value">{stats.assessments_done}</div>
          <div className="stat-card__sub">
            {stats.total_students > 0
              ? `${Math.round((stats.assessments_done / stats.total_students) * 100)}% completion`
              : 'No students yet'}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Need attention</div>
          <div className="stat-card__value" style={{ color: stats.students_needing_attention > 0 ? 'var(--color-warning)' : 'var(--color-text)' }}>
            {stats.students_needing_attention}
          </div>
          <div className="stat-card__sub">No quiz yet</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Notes written</div>
          <div className="stat-card__value">{stats.notes_written}</div>
          <div className="stat-card__sub">Across all students</div>
        </div>
      </div>

      <div className="dashboard-grid">
        <StudentList students={students} />

        <div className="dashboard-card">
          <p className="dashboard-card__title">Assessment progress</p>
          <AssessmentRing done={stats.assessments_done} total={stats.total_students} />
          <button className="btn-primary" style={{ width: '100%', marginTop: 'var(--space-4)' }}>
            Add a student note
          </button>
        </div>
      </div>
    </div>
  )
}
