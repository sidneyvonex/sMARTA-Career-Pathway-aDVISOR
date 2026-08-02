import { useMemo, useState, type FormEvent } from 'react'

import {
  GRADE_LEVEL_LABELS,
  GRADE_LEVEL_ORDER,
  type AcademicGoal,
  type AcademicGoalCreate,
  type AcademicGrade,
  type GradeLevel,
  type SubjectProgress,
} from '../../api/students'
import { useAcademicGoalMutations } from '../../hooks/useAcademicGoalMutations'


interface Props {
  goals: AcademicGoal[]
  subjects: SubjectProgress[]
  initiallyOpen?: boolean
}


const currentYear = new Date().getFullYear()


export default function AcademicTargetPanel({ goals, subjects, initiallyOpen = false }: Props) {
  const [open, setOpen] = useState(initiallyOpen)
  const [continuityCode, setContinuityCode] = useState(subjects[0]?.continuity_code ?? '')
  const [targetLevel, setTargetLevel] = useState<GradeLevel>('ME1')
  const [targetTerm, setTargetTerm] = useState<1 | 2 | 3>(1)
  const [targetYear, setTargetYear] = useState(currentYear)
  const [targetAcademicGrade, setTargetAcademicGrade] = useState<AcademicGrade>(10)
  const [actionPlan, setActionPlan] = useState('')
  const { create } = useAcademicGoalMutations()
  const activeGoals = goals.filter((goal) => goal.status === 'active')
  const subjectsWithoutTargets = useMemo(() => {
    const activeCodes = new Set(activeGoals.map((goal) => goal.continuity_code))
    return subjects.filter((item) => !activeCodes.has(item.continuity_code))
  }, [activeGoals, subjects])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const payload: AcademicGoalCreate = {
      continuity_code: continuityCode,
      target_level: targetLevel,
      target_term: targetTerm,
      target_year: targetYear,
      target_academic_grade: targetAcademicGrade,
      action_plan: actionPlan.trim(),
    }
    create.mutate(payload, {
      onSuccess: () => {
        setActionPlan('')
        setOpen(false)
      },
    })
  }

  return (
    <section className="progress-panel progress-targets" aria-labelledby="academic-targets-title">
      <div className="progress-section-heading">
        <div>
          <h2 id="academic-targets-title">Academic targets</h2>
          <p>Choose one practical improvement target for a subject.</p>
        </div>
        {!open && subjectsWithoutTargets.length > 0 && (
          <button type="button" className="student-action" onClick={() => {
            setContinuityCode(subjectsWithoutTargets[0].continuity_code)
            setOpen(true)
          }}>
            Set an academic target
          </button>
        )}
      </div>

      {activeGoals.length > 0 && (
        <div className="progress-target-list">
          {activeGoals.map((goal) => {
            const subjectName = subjects.find(
              (item) => item.continuity_code === goal.continuity_code,
            )?.subject_name ?? goal.continuity_code
            return (
              <article key={goal.id} className="progress-target">
                <div>
                  <strong>{subjectName}</strong>
                  <span>{GRADE_LEVEL_LABELS[goal.current_level.code]} to {GRADE_LEVEL_LABELS[goal.target_level.code]}</span>
                </div>
                <p>{goal.action_plan}</p>
                <small>Target: Grade {goal.target_academic_grade}, {goal.target_year}, Term {goal.target_term}</small>
              </article>
            )
          })}
        </div>
      )}

      {activeGoals.length === 0 && !open && (
        <p className="progress-panel__empty">You have no active academic targets yet.</p>
      )}

      {open && (
        <form className="progress-target-form" onSubmit={submit}>
          <div className="student-field">
            <label htmlFor="academic-target-subject">Subject</label>
            <select
              id="academic-target-subject"
              className="student-field__control"
              value={continuityCode}
              onChange={(event) => setContinuityCode(event.target.value)}
              required
            >
              {subjectsWithoutTargets.map((item) => (
                <option key={item.continuity_code} value={item.continuity_code}>{item.subject_name}</option>
              ))}
            </select>
          </div>
          <div className="student-field">
            <label htmlFor="academic-target-level">Target level</label>
            <select
              id="academic-target-level"
              className="student-field__control"
              value={targetLevel}
              onChange={(event) => setTargetLevel(event.target.value as GradeLevel)}
            >
              {GRADE_LEVEL_ORDER.map((level) => (
                <option key={level} value={level}>{level} - {GRADE_LEVEL_LABELS[level]}</option>
              ))}
            </select>
          </div>
          <div className="student-field">
            <label htmlFor="academic-target-term">Target term</label>
            <select
              id="academic-target-term"
              className="student-field__control"
              value={targetTerm}
              onChange={(event) => setTargetTerm(Number(event.target.value) as 1 | 2 | 3)}
            >
              <option value={1}>Term 1</option>
              <option value={2}>Term 2</option>
              <option value={3}>Term 3</option>
            </select>
          </div>
          <div className="student-field">
            <label htmlFor="academic-target-year">Target year</label>
            <input
              id="academic-target-year"
              className="student-field__control"
              type="number"
              min={currentYear}
              max={currentYear + 5}
              value={targetYear}
              onChange={(event) => setTargetYear(Number(event.target.value))}
              required
            />
          </div>
          <div className="student-field">
            <label htmlFor="academic-target-grade">Target academic grade</label>
            <select
              id="academic-target-grade"
              className="student-field__control"
              value={targetAcademicGrade}
              onChange={(event) => setTargetAcademicGrade(Number(event.target.value) as AcademicGrade)}
            >
              {[9, 10, 11, 12].map((grade) => <option key={grade} value={grade}>Grade {grade}</option>)}
            </select>
          </div>
          <div className="student-field progress-target-form__plan">
            <label htmlFor="academic-target-plan">Action plan</label>
            <textarea
              id="academic-target-plan"
              className="student-field__control"
              value={actionPlan}
              onChange={(event) => setActionPlan(event.target.value)}
              required
            />
          </div>
          <div className="progress-target-form__actions">
            <button type="submit" className="student-action" disabled={create.isPending || !continuityCode || !actionPlan.trim()}>
              {create.isPending ? 'Creating target…' : 'Create target'}
            </button>
            <button type="button" className="student-action student-action--secondary" onClick={() => setOpen(false)} disabled={create.isPending}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </section>
  )
}
