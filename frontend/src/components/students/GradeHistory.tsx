import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import toast from 'react-hot-toast'

import {
  type CBCGrade,
  GRADE_LEVEL_LABELS,
  GRADE_LEVEL_ORDER,
  studentsApi,
  type GradeLevel,
} from '../../api/students'
import { academicGoalKeys } from '../../hooks/useAcademicGoalMutations'

interface Props {
  grades: CBCGrade[]
  studentSubjectId?: number
}

interface GradeDraft {
  id: number
  term: 1 | 2 | 3
  year: number
  level: GradeLevel
}

function gradeErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ message?: unknown }>
  if (!axiosError.response) return 'Connection error. Please check your internet.'
  const status = axiosError.response.status
  if (status === 403) return "You don't have permission to do that."
  if (status === 404) return 'That item no longer exists.'
  if (status >= 500) return 'Server error. Please try again in a moment.'
  const message = axiosError.response.data?.message
  return typeof message === 'string' && message.trim()
    ? message
    : 'Something went wrong. Please try again.'
}

function isMutable(grade: CBCGrade, openPeriodKeys: Set<string>): boolean {
  return (
    !grade.verified_by
    && !grade.verified_school
    && !grade.verified_at
    && openPeriodKeys.has(`${grade.year}-${grade.term}`)
  )
}

function verificationLabel(grade: CBCGrade): string {
  if (grade.verified_at) return 'School verified'
  if (grade.verified_school) return 'Verification removed; school provenance retained'
  return 'Not school verified'
}

export default function GradeHistory({ grades, studentSubjectId }: Props) {
  const queryClient = useQueryClient()
  const periodsQ = useQuery({
    queryKey: ['students', 'academic-periods'],
    queryFn: () => studentsApi.getAcademicPeriods().then(response => response.data.data),
    enabled: studentSubjectId !== undefined,
  })
  const openPeriodKeys = new Set(
    (periodsQ.data ?? [])
      .filter(period => period.can_submit)
      .map(period => `${period.year}-${period.term}`),
  )
  const [draft, setDraft] = useState<GradeDraft | null>(null)
  const refreshEvidence = () => {
    queryClient.invalidateQueries({ queryKey: ['grades', studentSubjectId] })
    queryClient.invalidateQueries({ queryKey: ['students', 'academic-progress'] })
    queryClient.invalidateQueries({ queryKey: academicGoalKeys.all })
  }
  const update = useMutation({
    mutationFn: (value: GradeDraft) => studentsApi.updateGrade(
      studentSubjectId!,
      value.id,
      { term: value.term, year: value.year, level: value.level },
    ),
    onSuccess: () => {
      toast.success('Grade updated.')
      setDraft(null)
      refreshEvidence()
    },
    onError: (error) => toast.error(gradeErrorMessage(error)),
  })
  const remove = useMutation({
    mutationFn: (grade: CBCGrade) => studentsApi.deleteGrade(studentSubjectId!, grade.id),
    onSuccess: () => {
      toast.success('Grade entry removed.')
      refreshEvidence()
    },
    onError: (error) => toast.error(gradeErrorMessage(error)),
  })

  if (grades.length === 0) {
    return <p className="grade-history__empty">No grades entered yet. Your first result will appear here.</p>
  }

  return (
    <div className="grade-history__table-wrap">
      <table className="grade-history">
        <thead>
          <tr>
            <th>Term</th>
            <th>Year</th>
            <th>Level</th>
            <th>Source</th>
            <th>Verification</th>
            {studentSubjectId !== undefined && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {grades.map((grade) => {
            const editing = draft?.id === grade.id
            const label = `Term ${grade.term} ${grade.year}`
            return (
            <tr key={grade.id}>
              <td>Term {grade.term}</td>
              <td>{grade.year}</td>
              <td>
                {editing ? (
                  <select
                    aria-label={`Edit level for ${label}`}
                    value={draft.level}
                    onChange={(event) => setDraft({ ...draft, level: event.target.value as GradeLevel })}
                    disabled={update.isPending}
                  >
                    {GRADE_LEVEL_ORDER.map((level) => (
                      <option key={level} value={level}>{level} — {GRADE_LEVEL_LABELS[level]}</option>
                    ))}
                  </select>
                ) : (
                  <span className={`grade-level grade-level--${grade.level.slice(0, 2).toLowerCase()}`}>
                    {GRADE_LEVEL_LABELS[grade.level]}
                  </span>
                )}
              </td>
              <td>
                <span className="grade-provenance">
                  {grade.source === 'school' ? 'School entered' : 'Learner entered'}
                </span>
              </td>
              <td>
                <span
                  className={`grade-verification ${
                    grade.verified_at
                      ? 'grade-verification--verified'
                      : 'grade-verification--unverified'
                  }`}
                >
                  {verificationLabel(grade)}
                </span>
              </td>
              {studentSubjectId !== undefined && (
                <td>
                  {editing ? (
                    <div className="grade-history__actions">
                      <label className="sr-only" htmlFor={`edit-term-${grade.id}`}>Edit term for {label}</label>
                      <select
                        id={`edit-term-${grade.id}`}
                        value={draft.term}
                        onChange={(event) => setDraft({ ...draft, term: Number(event.target.value) as 1 | 2 | 3 })}
                        disabled={update.isPending}
                      >
                        <option value={1} disabled={!openPeriodKeys.has(`${draft.year}-1`)}>Term 1</option>
                        <option value={2} disabled={!openPeriodKeys.has(`${draft.year}-2`)}>Term 2</option>
                        <option value={3} disabled={!openPeriodKeys.has(`${draft.year}-3`)}>Term 3</option>
                      </select>
                      <label className="sr-only" htmlFor={`edit-year-${grade.id}`}>Edit year for {label}</label>
                      <select
                        id={`edit-year-${grade.id}`}
                        value={draft.year}
                        onChange={(event) => {
                          const nextYear = Number(event.target.value)
                          const availableTerms = (periodsQ.data ?? [])
                            .filter(period => period.can_submit && period.year === nextYear)
                            .map(period => period.term)
                          setDraft({
                            ...draft,
                            year: nextYear,
                            term: availableTerms.includes(draft.term)
                              ? draft.term
                              : (availableTerms[0] ?? draft.term),
                          })
                        }}
                        disabled={update.isPending}
                      >
                        {[...new Set(
                          (periodsQ.data ?? [])
                            .filter(period => period.can_submit)
                            .map(period => period.year),
                        )].map(openYear => (
                          <option key={openYear} value={openYear}>{openYear}</option>
                        ))}
                      </select>
                      <button type="button" onClick={() => update.mutate(draft)} disabled={update.isPending}>
                        {update.isPending ? 'Saving…' : 'Save grade changes'}
                      </button>
                      <button type="button" onClick={() => setDraft(null)} disabled={update.isPending}>
                        Cancel
                      </button>
                    </div>
                  ) : isMutable(grade, openPeriodKeys) ? (
                    <div className="grade-history__actions">
                      <button
                        type="button"
                        aria-label={`Edit ${label}`}
                        onClick={() => setDraft({
                          id: grade.id,
                          term: grade.term,
                          year: grade.year,
                          level: grade.level,
                        })}
                        disabled={remove.isPending}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        aria-label={`Delete ${label}`}
                        onClick={() => {
                          if (window.confirm(`Delete ${label}? This grade entry cannot be recovered.`)) {
                            remove.mutate(grade)
                          }
                        }}
                        disabled={remove.isPending}
                      >
                        Delete
                      </button>
                    </div>
                  ) : (
                    <span className="grade-history__locked">
                      {periodsQ.isLoading ? 'Checking window' : 'History locked'}
                    </span>
                  )}
                </td>
              )}
            </tr>
          )})}
        </tbody>
      </table>
    </div>
  )
}
