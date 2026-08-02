import { useState } from 'react'

import type { EducationGoal, EducationGoalKind } from '../../api/tertiary'
import { useEducationGoalMutations } from '../../hooks/useEducationGoalMutations'


function slotValue(kind: EducationGoalKind, priority: 1 | 2) {
  return kind === 'primary' ? 'primary' : `alternative-${priority}`
}


function slotParts(value: string): { kind: EducationGoalKind; priority: 1 | 2 } {
  if (value === 'primary') return { kind: 'primary', priority: 1 }
  return { kind: 'alternative', priority: value === 'alternative-2' ? 2 : 1 }
}


function GoalCard({ goal }: { goal: EducationGoal }) {
  const [slot, setSlot] = useState(slotValue(goal.kind, goal.priority))
  const { update, remove } = useEducationGoalMutations()
  const label = goal.kind === 'primary' ? 'Primary' : `Alternative ${goal.priority}`

  return (
    <article className="education-goal-card" aria-label={`${label} education goal`}>
      <div className="education-goal-card__copy">
        <span>{label}</span>
        <h3>{goal.institution.name}</h3>
        <p>{goal.programme?.name ?? 'Institution-wide exploration'}</p>
        <small>
          {goal.institution.education_framework} · {goal.institution.admission_cycle} ·{' '}
          {goal.institution.verification_status === 'historical' ? 'Historical reference' : 'Catalogue reference'}
        </small>
      </div>
      <div className="education-goal-card__actions">
        <div className="student-field">
          <label htmlFor={`goal-slot-${goal.id}`}>Change goal slot</label>
          <select
            id={`goal-slot-${goal.id}`}
            className="student-field__control"
            value={slot}
            onChange={(event) => setSlot(event.target.value)}
            disabled={update.isPending || remove.isPending}
          >
            <option value="primary">Primary</option>
            <option value="alternative-1">Alternative 1</option>
            <option value="alternative-2">Alternative 2</option>
          </select>
        </div>
        <div className="education-goal-card__buttons">
          <button
            type="button"
            className="student-action student-action--secondary"
            disabled={update.isPending || remove.isPending}
            onClick={() => update.mutate({ goalId: goal.id, data: slotParts(slot) })}
          >
            {update.isPending ? 'Updating…' : 'Update goal'}
          </button>
          <button
            type="button"
            className="education-action-danger"
            disabled={update.isPending || remove.isPending}
            onClick={() => remove.mutate(goal.id)}
          >
            {remove.isPending ? 'Removing…' : 'Remove goal'}
          </button>
        </div>
      </div>
    </article>
  )
}


export default function EducationGoalList({ goals }: { goals: EducationGoal[] }) {
  return <div className="education-goal-list">{goals.map((goal) => <GoalCard key={goal.id} goal={goal} />)}</div>
}
