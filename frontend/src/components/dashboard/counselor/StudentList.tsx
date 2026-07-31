import type { AssignedStudent } from '../../../api/dashboard'
import ActionCard from '../../common/dashboard/ActionCard'
import EmptyState from '../../common/dashboard/EmptyState'
import SectionHeader from '../../common/dashboard/SectionHeader'
import StatusBadge from '../../common/dashboard/StatusBadge'

interface Props {
  students: AssignedStudent[]
}

export default function StudentList({ students }: Props) {
  if (students.length === 0) {
    return (
      <EmptyState
        title="No students assigned"
        description="New learner assignments will appear in this caseload."
      />
    )
  }

  return (
    <div className="db-panel db-panel--compact db-stack">
      <SectionHeader
        eyebrow="Caseload"
        title="My students"
        action={students.length > 5
          ? { label: `View all ${students.length}`, to: '/counselor/students' }
          : undefined}
      />
      <div className="db-stack db-stack--tight">
        {students.slice(0, 5).map((student) => (
          <ActionCard
            key={student.id}
            title={`${student.first_name} ${student.last_name}`}
            description={`Grade ${student.grade}${student.top_pathway ? ` · ${student.top_pathway}` : ''}`}
            to={`/counselor/students/${student.id}`}
            status={(
              <StatusBadge tone={student.quiz_status === 'done' ? 'positive' : 'warning'}>
                {student.quiz_status === 'done' ? 'Assessed' : 'Pending'}
              </StatusBadge>
            )}
          />
        ))}
      </div>
    </div>
  )
}
