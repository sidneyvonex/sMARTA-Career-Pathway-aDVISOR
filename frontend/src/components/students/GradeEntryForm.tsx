import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi, GradeLevel, GRADE_LEVEL_LABELS } from '../../api/students'

interface Props {
  studentSubjectId: number
}

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: 6 }, (_, index) => CURRENT_YEAR - 5 + index + 1).reverse()

export default function GradeEntryForm({ studentSubjectId }: Props) {
  const [term, setTerm] = useState<1 | 2 | 3>(1)
  const [year, setYear] = useState(CURRENT_YEAR)
  const [level, setLevel] = useState<GradeLevel>('ME1')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => studentsApi.addGrade(studentSubjectId, { term, year, level }),
    onSuccess: () => {
      toast.success('Grade added.')
      queryClient.invalidateQueries({ queryKey: ['grades', studentSubjectId] })
    },
    onError: () => toast.error('Could not add grade. That term/year may already have a grade.'),
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
          {(Object.keys(GRADE_LEVEL_LABELS) as GradeLevel[]).map((key) => (
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
