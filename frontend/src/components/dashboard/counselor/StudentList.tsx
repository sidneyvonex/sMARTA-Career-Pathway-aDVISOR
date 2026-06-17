import type { AssignedStudent } from '../../../api/dashboard'
import { initials } from '../../../lib/format'

interface Props {
  students: AssignedStudent[]
}

function statusClass(s: AssignedStudent) {
  if (s.quiz_status === 'done') return 'status-badge--assessed'
  return 'status-badge--pending'
}

function statusLabel(s: AssignedStudent) {
  return s.quiz_status === 'done' ? 'Assessed' : 'Pending'
}

export default function StudentList({ students }: Props) {
  if (students.length === 0) {
    return (
      <div className="dashboard-card">
        <p className="dashboard-card__title">My students</p>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          No students assigned yet.
        </p>
      </div>
    )
  }

  return (
    <div className="dashboard-card">
      <p className="dashboard-card__title">My students</p>
      <ul style={{ listStyle: 'none' }}>
        {students.slice(0, 5).map((s) => (
          <li key={s.id} className="student-list-item">
            <div className="student-list-item__avatar" aria-hidden="true">{initials(s.first_name, s.last_name)}</div>
            <div className="student-list-item__info">
              <div className="student-list-item__name">{s.first_name} {s.last_name}</div>
              <div className="student-list-item__sub">
                Grade {s.grade}{s.top_pathway ? ` · ${s.top_pathway}` : ''}
              </div>
            </div>
            <span className={`status-badge ${statusClass(s)}`}>{statusLabel(s)}</span>
          </li>
        ))}
      </ul>
      {students.length > 5 && (
        <p style={{ marginTop: 'var(--space-3)', fontSize: 'var(--font-size-sm)', color: 'var(--color-primary)' }}>
          View all {students.length} students
        </p>
      )}
    </div>
  )
}
