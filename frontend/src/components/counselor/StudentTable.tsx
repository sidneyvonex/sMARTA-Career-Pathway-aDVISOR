import { Link } from 'react-router-dom'
import type { AssignedStudent } from '../../api/dashboard'
import { initials, formatRelativeTime } from '../../lib/format'

interface Props {
  students: AssignedStudent[]
}

function isNewStudent(lastActive: string | null): boolean {
  if (!lastActive) return false
  return Date.now() - new Date(lastActive).getTime() < 14 * 24 * 60 * 60 * 1000
}

function statusBadgeClass(s: AssignedStudent) {
  if (s.quiz_status === 'done') return 'status-badge status-badge--assessed'
  if (isNewStudent(s.last_active)) return 'status-badge status-badge--new'
  return 'status-badge status-badge--pending'
}

function statusLabel(s: AssignedStudent) {
  if (s.quiz_status === 'done') return 'Assessed'
  if (isNewStudent(s.last_active)) return 'New'
  return 'Pending'
}

export default function StudentTable({ students }: Props) {
  if (students.length === 0) {
    return (
      <div className="student-table-wrap">
        <p className="table-empty">No students match this filter.</p>
      </div>
    )
  }

  return (
    <div className="student-table-wrap">
      <table className="student-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Student</th>
            <th>Grade</th>
            <th>Status</th>
            <th>Best pathway</th>
            <th>Fit %</th>
            <th>Last active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s, i) => (
            <tr key={s.id}>
              <td>{i + 1}</td>
              <td>
                <div className="student-cell">
                  <div className="student-cell__avatar" aria-hidden="true">
                    {initials(s.first_name, s.last_name)}
                  </div>
                  <span className="student-cell__name">
                    {s.first_name} {s.last_name}
                  </span>
                </div>
              </td>
              <td>{s.grade}</td>
              <td>
                <span className={statusBadgeClass(s)}>{statusLabel(s)}</span>
              </td>
              <td>{s.top_pathway ?? '--'}</td>
              <td>
                {s.fit_pct != null ? (
                  <span className="fit-pct">{s.fit_pct}%</span>
                ) : (
                  <span className="fit-pct fit-pct--na">--</span>
                )}
              </td>
              <td>
                {s.last_active ? formatRelativeTime(s.last_active) : '--'}
              </td>
              <td>
                <Link to={`/counselor/students/${s.id}`} className="view-link">
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
