import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi, GradeLevel, GRADE_LEVEL_LABELS } from '../../api/students'

interface Props {
  studentSubjectId: number
}

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: 6 }, (_, i) => CURRENT_YEAR - 5 + i + 1).reverse()

export default function GradeEntryForm({ studentSubjectId }: Props) {
  const [term, setTerm] = useState<1 | 2 | 3>(1)
  const [year, setYear] = useState(CURRENT_YEAR)
  const [level, setLevel] = useState<GradeLevel>('ME1')
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => studentsApi.addGrade(studentSubjectId, { term, year, level }),
    onSuccess: () => {
      toast.success('Grade added.')
      qc.invalidateQueries({ queryKey: ['grades', studentSubjectId] })
    },
    onError: () => toast.error('Could not add grade. That term/year may already have a grade.'),
  })

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
      style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}
    >
      <div>
        <label htmlFor="term" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600 }}>Term</label>
        <select id="term" value={term} onChange={(e) => setTerm(Number(e.target.value) as 1 | 2 | 3)}
          style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
          <option value={1}>Term 1</option>
          <option value={2}>Term 2</option>
          <option value={3}>Term 3</option>
        </select>
      </div>

      <div>
        <label htmlFor="year" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600 }}>Year</label>
        <select id="year" value={year} onChange={(e) => setYear(Number(e.target.value))}
          style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
          {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      <div>
        <label htmlFor="level" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600 }}>Level</label>
        <select id="level" value={level} onChange={(e) => setLevel(e.target.value as GradeLevel)}
          style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
          {(Object.keys(GRADE_LEVEL_LABELS) as GradeLevel[]).map((k) => (
            <option key={k} value={k}>{k} — {GRADE_LEVEL_LABELS[k]}</option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        style={{ padding: '0.45rem 1rem', background: 'var(--color-primary)', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
      >
        {mutation.isPending ? 'Adding…' : 'Add Grade'}
      </button>
    </form>
  )
}
