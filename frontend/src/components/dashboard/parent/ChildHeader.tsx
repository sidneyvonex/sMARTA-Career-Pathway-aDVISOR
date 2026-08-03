import type { LinkedChild } from '../../../api/dashboard'
import { formatCounty, initials } from '../../../lib/format'

interface Props {
  child: LinkedChild
}

function formatDate(iso: string | null) {
  if (!iso) return 'Unknown'
  return new Date(iso).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function ChildHeader({ child }: Props) {
  return (
    <div className="child-header-card" role="region" aria-label="Your child's overview">
      <div className="greeting-strip__avatar child-header-card__avatar" aria-hidden="true">
        {initials(child.first_name, child.last_name)}
      </div>
      <div className="greeting-strip__body">
        <div className="greeting-strip__name">{child.first_name} {child.last_name}</div>
        <div className="greeting-strip__chips">
          <span className="greeting-chip">Grade {child.grade}</span>
          {child.county && <span className="greeting-chip child-header-card__county">{formatCounty(child.county)}</span>}
          <span className={`greeting-chip${child.quiz_status === 'done' ? ' greeting-chip--gold' : ''}`}>
            {child.quiz_status === 'done' ? 'Interest quiz done' : 'Interest quiz still to do'}
          </span>
          <span className="greeting-chip">Tracking {child.subject_count} subjects</span>
          <span className="greeting-chip">
            {child.counselor_assigned ? 'Has a school counsellor' : 'No counsellor yet'}
          </span>
        </div>
        <div className="child-header-card__active">
          Last active: {formatDate(child.last_active)}
        </div>
      </div>
    </div>
  )
}
