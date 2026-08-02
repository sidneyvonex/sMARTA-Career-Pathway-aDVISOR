import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import toast from 'react-hot-toast'
import {
  studentsApi,
  GradeLevel,
  GRADE_LEVEL_LABELS,
  GRADE_LEVEL_ORDER,
} from '../../api/students'
import { academicGoalKeys } from '../../hooks/useAcademicGoalMutations'

interface Props {
  studentSubjectId: number
}

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: 6 }, (_, index) => CURRENT_YEAR - 5 + index + 1).reverse()

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

export default function GradeEntryForm({ studentSubjectId }: Props) {
  const [term, setTerm] = useState<1 | 2 | 3>(1)
  const [year, setYear] = useState(CURRENT_YEAR)
  const [level, setLevel] = useState<GradeLevel>('ME1')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => studentsApi.addGrade(studentSubjectId, { term, year, level }),
    onSuccess: () => {
      toast.success(`Grade saved for Term ${term}.`)
      queryClient.invalidateQueries({ queryKey: ['grades', studentSubjectId] })
      queryClient.invalidateQueries({ queryKey: ['students', 'academic-progress'] })
      queryClient.invalidateQueries({ queryKey: academicGoalKeys.all })
    },
    onError: (error) => toast.error(gradeErrorMessage(error)),
  })

  return (
    <form
      onSubmit={(event) => { event.preventDefault(); mutation.mutate() }}
      className="grade-entry-form"
    >
      <div className="student-field">
        <label htmlFor="term">Term</label>
        <select
          id="term"
          value={term}
          onChange={(event) => setTerm(Number(event.target.value) as 1 | 2 | 3)}
          className="student-field__control"
        >
          <option value={1}>Term 1</option>
          <option value={2}>Term 2</option>
          <option value={3}>Term 3</option>
        </select>
      </div>

      <div className="student-field">
        <label htmlFor="year">Year</label>
        <select
          id="year"
          value={year}
          onChange={(event) => setYear(Number(event.target.value))}
          className="student-field__control"
        >
          {YEARS.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </div>

      <div className="student-field student-field--wide">
        <label htmlFor="level">Level</label>
        <select
          id="level"
          value={level}
          onChange={(event) => setLevel(event.target.value as GradeLevel)}
          className="student-field__control"
        >
          {GRADE_LEVEL_ORDER.map((key) => (
            <option key={key} value={key}>{key} — {GRADE_LEVEL_LABELS[key]}</option>
          ))}
        </select>
      </div>

      <button type="submit" disabled={mutation.isPending} className="student-action">
        {mutation.isPending ? 'Adding…' : 'Add grade'}
      </button>
    </form>
  )
}
