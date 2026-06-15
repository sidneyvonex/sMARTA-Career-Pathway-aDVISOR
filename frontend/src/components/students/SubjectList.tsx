import { StudentSubject } from '../../api/students'

interface Props {
  enrolledSubjects: StudentSubject[]
  onRemove: (id: number) => void
}

export default function SubjectList({ enrolledSubjects, onRemove }: Props) {
  if (enrolledSubjects.length === 0) {
    return <p style={{ color: 'var(--color-text-secondary)' }}>No subjects added yet.</p>
  }
  return (
    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
      {enrolledSubjects.map((ss) => (
        <li
          key={ss.id}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0', borderBottom: '1px solid var(--color-border)' }}
        >
          <span>
            <strong>{ss.subject.name}</strong>{' '}
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>({ss.subject.category})</span>
          </span>
          <button
            type="button"
            onClick={() => {
              if (window.confirm(`Remove ${ss.subject.name}? All grades for this subject will be deleted.`)) {
                onRemove(ss.id)
              }
            }}
            style={{ color: 'var(--color-error)', background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Remove
          </button>
        </li>
      ))}
    </ul>
  )
}
