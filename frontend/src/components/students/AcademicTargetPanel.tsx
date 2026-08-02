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
import LoadingSkeleton from '../common/dashboard/LoadingSkeleton'


interface Props {
  goals: AcademicGoal[]
  subjects: SubjectProgress[]
  initiallyOpen?: boolean
  isLoading?: boolean
}


const currentYear = new Date().getFullYear()
const academicGrades = [9, 10, 11, 12] satisfies AcademicGrade[]


function subjectName(subjects: SubjectProgress[], continuityCode: string): string {
  return subjects.find((item) => item.continuity_code === continuityCode)?.subject_name
    ?? continuityCode
}


function allowedLevels(currentLevel: GradeLevel): GradeLevel[] {
  const currentIndex = GRADE_LEVEL_ORDER.indexOf(currentLevel)
  return currentIndex < 0
    ? GRADE_LEVEL_ORDER
    : GRADE_LEVEL_ORDER.slice(0, currentIndex + 1)
}


export default function AcademicTargetPanel({
  goals,
  subjects,
  initiallyOpen = false,
  isLoading = false,
}: Props) {
  const [open, setOpen] = useState(initiallyOpen)
  const [continuityCode, setContinuityCode] = useState(subjects[0]?.continuity_code ?? '')
  const [targetLevel, setTargetLevel] = useState<GradeLevel>('ME1')
  const [targetTerm, setTargetTerm] = useState<1 | 2 | 3>(1)
  const [targetYear, setTargetYear] = useState(currentYear)
  const [targetAcademicGrade, setTargetAcademicGrade] = useState<AcademicGrade>(10)
  const [actionPlan, setActionPlan] = useState('')
  const [editingGoalId, setEditingGoalId] = useState<number | null>(null)
  const { create, update, close, confirmAchievement } = useAcademicGoalMutations()
  const activeGoals = goals.filter((goal) => goal.status === 'active')
  const historyGoals = goals.filter((goal) => goal.status !== 'active')
  const subjectsWithoutTargets = useMemo(() => {
    const activeCodes = new Set(activeGoals.map((goal) => goal.continuity_code))
    return subjects.filter((item) => (
      !activeCodes.has(item.continuity_code)
      && item.evidence.length > 0
      && allowedLevels(item.evidence[item.evidence.length - 1].level).length > 0
    ))
  }, [activeGoals, subjects])
  const editingGoal = goals.find((goal) => goal.id === editingGoalId) ?? null
  const selectedSubject = subjects.find(
    (item) => item.continuity_code === continuityCode,
  ) ?? null
  const baseline = editingGoal
    ? {
        level: editingGoal.current_level.code,
        period: editingGoal.creation_evidence_snapshot.period,
      }
    : selectedSubject?.evidence.length
      ? {
          level: selectedSubject.evidence[selectedSubject.evidence.length - 1].level,
          period: {
            academic_grade: selectedSubject.evidence[selectedSubject.evidence.length - 1].academic_grade,
            year: selectedSubject.evidence[selectedSubject.evidence.length - 1].year,
            term: selectedSubject.evidence[selectedSubject.evidence.length - 1].term,
          },
        }
      : null
  const levelChoices = baseline ? allowedLevels(baseline.level) : GRADE_LEVEL_ORDER
  const gradeChoices = baseline
    ? academicGrades.filter((grade) => grade >= baseline.period.academic_grade)
    : academicGrades
  const termChoices = ([1, 2, 3] as const).filter((term) => (
    !baseline
    || targetAcademicGrade > baseline.period.academic_grade
    || targetYear > baseline.period.year
    || term > baseline.period.term
  ))
  const mutationPending = (
    create.isPending || update.isPending || close.isPending ||
    confirmAchievement.isPending
  )

  const resetForm = () => {
    setOpen(false)
    setEditingGoalId(null)
    setActionPlan('')
  }

  const startCreate = () => {
    const subject = subjectsWithoutTargets[0]
    const latest = subject?.evidence[subject.evidence.length - 1]
    if (!subject || !latest) return
    const nextTerm = latest.term < 3 ? (latest.term + 1) as 2 | 3 : 1
    const nextGrade = latest.term === 3 && latest.academic_grade < 12
      ? (latest.academic_grade + 1) as AcademicGrade
      : latest.academic_grade
    setEditingGoalId(null)
    setContinuityCode(subject.continuity_code)
    setTargetLevel(allowedLevels(latest.level)[0])
    setTargetTerm(nextTerm)
    setTargetYear(latest.term === 3 ? Math.max(currentYear, latest.year + 1) : Math.max(currentYear, latest.year))
    setTargetAcademicGrade(nextGrade)
    setActionPlan('')
    setOpen(true)
  }

  const startEdit = (goal: AcademicGoal) => {
    setEditingGoalId(goal.id)
    setContinuityCode(goal.continuity_code)
    setTargetLevel(goal.target_level.code)
    setTargetTerm(goal.target_term)
    setTargetYear(goal.target_year)
    setTargetAcademicGrade(goal.target_academic_grade)
    setActionPlan(goal.action_plan)
    setOpen(true)
  }

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
    const onSuccess = () => resetForm()
    if (editingGoalId !== null) {
      update.mutate({
        goalId: editingGoalId,
        data: {
          target_level: payload.target_level,
          target_term: payload.target_term,
          target_year: payload.target_year,
          target_academic_grade: payload.target_academic_grade,
          action_plan: payload.action_plan,
        },
      }, { onSuccess })
      return
    }
    create.mutate(payload, {
      onSuccess: () => {
        resetForm()
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
        {!isLoading && !open && subjectsWithoutTargets.length > 0 && (
          <button type="button" className="student-action" onClick={startCreate}>
            Set an academic target
          </button>
        )}
      </div>

      {isLoading ? (
        <LoadingSkeleton label="Loading academic targets" rows={2} variant="list" />
      ) : (
        <>
      {activeGoals.length > 0 && (
        <div className="progress-target-list">
          {activeGoals.map((goal) => {
            const name = subjectName(subjects, goal.continuity_code)
            return (
              <article key={goal.id} className="progress-target">
                <div>
                  <strong>{name}</strong>
                  <span>{GRADE_LEVEL_LABELS[goal.current_level.code]} to {GRADE_LEVEL_LABELS[goal.target_level.code]}</span>
                </div>
                <p>{goal.action_plan}</p>
                <small>Target: Grade {goal.target_academic_grade}, {goal.target_year}, Term {goal.target_term}</small>
                <span className={`progress-target__readiness${goal.ready_for_achievement ? ' is-ready' : ''}`}>
                  {goal.ready_for_achievement
                    ? 'Ready to confirm achievement'
                    : 'Waiting for later evidence'}
                </span>
                <div className="progress-target__actions">
                  <button
                    type="button"
                    className="student-action student-action--secondary"
                    aria-label={`Edit ${name} target`}
                    onClick={() => startEdit(goal)}
                    disabled={mutationPending}
                  >
                    Edit
                  </button>
                  {goal.ready_for_achievement && (
                    <button
                      type="button"
                      className="student-action"
                      aria-label={`Confirm ${name} achieved`}
                      onClick={() => {
                        if (window.confirm(`Confirm that ${name} has achieved this target using the latest qualifying evidence?`)) {
                          confirmAchievement.mutate(goal.id)
                        }
                      }}
                      disabled={mutationPending}
                    >
                      {confirmAchievement.isPending ? 'Confirming…' : 'Confirm achieved'}
                    </button>
                  )}
                  <button
                    type="button"
                    className="student-action student-action--secondary"
                    aria-label={`Close ${name} target`}
                    onClick={() => {
                      if (window.confirm(`Close the ${name} target? It will remain in target history.`)) {
                        close.mutate(goal.id)
                      }
                    }}
                    disabled={mutationPending}
                  >
                    {close.isPending ? 'Closing…' : 'Close'}
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      )}

      {activeGoals.length === 0 && !open && (
        <p className="progress-panel__empty">You have no active academic targets yet.</p>
      )}

      {historyGoals.length > 0 && (
        <section className="progress-target-history" aria-labelledby="target-history-title">
          <h3 id="target-history-title">Target history</h3>
          <div className="progress-target-list">
            {historyGoals.map((goal) => (
              <article key={goal.id} className="progress-target">
                <div>
                  <strong>{subjectName(subjects, goal.continuity_code)}</strong>
                  <span>{goal.status === 'achieved' ? 'Achieved' : 'Closed'}</span>
                </div>
                <p>{goal.action_plan}</p>
                <small>Target: Grade {goal.target_academic_grade}, {goal.target_year}, Term {goal.target_term}</small>
              </article>
            ))}
          </div>
        </section>
      )}

      {open && (
        <form className="progress-target-form" onSubmit={submit}>
          <div className="student-field">
            <label htmlFor="academic-target-subject">Subject</label>
            <select
              id="academic-target-subject"
              className="student-field__control"
              value={continuityCode}
              onChange={(event) => {
                const code = event.target.value
                const subject = subjects.find((item) => item.continuity_code === code)
                const latest = subject?.evidence[subject.evidence.length - 1]
                setContinuityCode(code)
                if (latest) setTargetLevel(allowedLevels(latest.level)[0])
              }}
              disabled={editingGoalId !== null || mutationPending}
              required
            >
              {editingGoal ? (
                <option value={editingGoal.continuity_code}>
                  {subjectName(subjects, editingGoal.continuity_code)}
                </option>
              ) : subjectsWithoutTargets.map((item) => (
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
              disabled={mutationPending}
            >
              {levelChoices.map((level) => (
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
              disabled={mutationPending}
            >
              {termChoices.map((term) => <option key={term} value={term}>Term {term}</option>)}
            </select>
          </div>
          <div className="student-field">
            <label htmlFor="academic-target-year">Target year</label>
            <input
              id="academic-target-year"
              className="student-field__control"
              type="number"
              min={baseline?.period.year ?? currentYear}
              max={Math.max(currentYear, baseline?.period.year ?? currentYear) + 5}
              value={targetYear}
              onChange={(event) => setTargetYear(Number(event.target.value))}
              required
              disabled={mutationPending}
            />
          </div>
          <div className="student-field">
            <label htmlFor="academic-target-grade">Target academic grade</label>
            <select
              id="academic-target-grade"
              className="student-field__control"
              value={targetAcademicGrade}
              onChange={(event) => {
                const grade = Number(event.target.value) as AcademicGrade
                setTargetAcademicGrade(grade)
                if (baseline && grade === baseline.period.academic_grade && targetYear === baseline.period.year && targetTerm <= baseline.period.term) {
                  setTargetTerm(Math.min(3, baseline.period.term + 1) as 1 | 2 | 3)
                }
              }}
              disabled={mutationPending}
            >
              {gradeChoices.map((grade) => <option key={grade} value={grade}>Grade {grade}</option>)}
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
              disabled={mutationPending}
            />
          </div>
          <div className="progress-target-form__actions">
            <button type="submit" className="student-action" disabled={mutationPending || !continuityCode || !actionPlan.trim()}>
              {editingGoalId !== null
                ? update.isPending ? 'Updating target…' : 'Update target'
                : create.isPending ? 'Creating target…' : 'Create target'}
            </button>
            <button type="button" className="student-action student-action--secondary" onClick={resetForm} disabled={mutationPending}>
              Cancel
            </button>
          </div>
        </form>
      )}
        </>
      )}
    </section>
  )
}
