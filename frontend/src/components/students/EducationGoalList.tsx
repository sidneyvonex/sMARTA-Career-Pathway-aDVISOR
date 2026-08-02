import { useEffect, useState } from 'react'

import type { EducationGoal, EducationGoalKind } from '../../api/tertiary'
import { useEducationGoalMutations } from '../../hooks/useEducationGoalMutations'


function slotValue(kind: EducationGoalKind, priority: 1 | 2) {
  return kind === 'primary' ? 'primary' : `alternative-${priority}`
}


function slotParts(value: string): { kind: EducationGoalKind; priority: 1 | 2 } {
  if (value === 'primary') return { kind: 'primary', priority: 1 }
  return { kind: 'alternative', priority: value === 'alternative-2' ? 2 : 1 }
}


function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(value))
}


const slotLabels = {
  primary: 'Primary',
  'alternative-1': 'Alternative 1',
  'alternative-2': 'Alternative 2',
}


function GoalCard({ goal, usedSlots }: { goal: EducationGoal; usedSlots: Set<string> }) {
  const currentSlot = slotValue(goal.kind, goal.priority)
  const [slot, setSlot] = useState(currentSlot)
  const { update, remove } = useEducationGoalMutations()
  const label = goal.kind === 'primary' ? 'Primary' : `Alternative ${goal.priority}`
  const provenance = goal.programme ?? goal.institution
  const verification = provenance.verification_status === 'historical'
    ? 'Historical'
    : provenance.verification_status === 'verified' ? 'Verified' : 'Unavailable'

  useEffect(() => setSlot(currentSlot), [currentSlot])

  return (
    <article className="education-goal-card" aria-label={`${label} education goal`}>
      <div className="education-goal-card__copy">
        <span>{label}</span>
        <h3>{goal.institution.name}</h3>
        <p>{goal.programme?.name ?? 'Institution-wide exploration'}</p>
        <small>
          {provenance.education_framework} · {provenance.admission_cycle} · Effective {displayDate(provenance.effective_date)} · Verification: {verification}
          {provenance.verification_status === 'historical' ? ' · Historical reference only' : ''}
        </small>
        <a href={provenance.source_url} target="_blank" rel="noreferrer" className="education-reference-source">
          Open {goal.programme ? 'programme' : 'institution'} source
        </a>
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
            {Object.entries(slotLabels).map(([value, optionLabel]) => {
              const occupied = value !== currentSlot && usedSlots.has(value)
              return (
                <option key={value} value={value} disabled={occupied}>
                  {optionLabel}{occupied ? ' (already used)' : ''}
                </option>
              )
            })}
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


export default function EducationGoalList({ goals, usedSlots }: { goals: EducationGoal[]; usedSlots: Set<string> }) {
  return (
    <div className="education-goal-list">
      {goals.map((goal) => <GoalCard key={goal.id} goal={goal} usedSlots={usedSlots} />)}
    </div>
  )
}
