import { CBCGrade, GRADE_LEVEL_LABELS } from '../../api/students'

interface Props {
  grades: CBCGrade[]
}

export default function GradeHistory({ grades }: Props) {
  if (grades.length === 0) {
    return <p style={{ color: 'var(--color-text-secondary)' }}>No grades entered yet.</p>
  }
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
      <thead>
        <tr style={{ background: 'var(--color-background)', textAlign: 'left' }}>
          <th style={{ padding: '0.5rem', borderBottom: '2px solid var(--color-border)' }}>Term</th>
          <th style={{ padding: '0.5rem', borderBottom: '2px solid var(--color-border)' }}>Year</th>
          <th style={{ padding: '0.5rem', borderBottom: '2px solid var(--color-border)' }}>Level</th>
        </tr>
      </thead>
      <tbody>
        {grades.map((g) => (
          <tr key={g.id}>
            <td style={{ padding: '0.5rem', borderBottom: '1px solid var(--color-border)' }}>Term {g.term}</td>
            <td style={{ padding: '0.5rem', borderBottom: '1px solid var(--color-border)' }}>{g.year}</td>
            <td style={{ padding: '0.5rem', borderBottom: '1px solid var(--color-border)' }}>{GRADE_LEVEL_LABELS[g.level]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
