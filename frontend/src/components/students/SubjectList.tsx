import { StudentSubject } from '../../api/students'

interface Props {
  enrolledSubjects: StudentSubject[]
  onRemove: (subject: StudentSubject) => void
  disabled?: boolean
}

export default function SubjectList({ enrolledSubjects, onRemove, disabled = false }: Props) {
  if (enrolledSubjects.length === 0) {
    return (
      <div className="student-empty-state student-empty-state--small">
        <span className="student-empty-state__icon" aria-hidden="true">＋</span>
        <strong>No subjects added yet</strong>
        <p>Choose from the subject list below to begin tracking.</p>
      </div>
    )
  }

  return (
    <ul className="subject-list">
      {enrolledSubjects.map((studentSubject) => (
        <li key={studentSubject.id} className="subject-list__item">
          <span className="subject-list__monogram" aria-hidden="true">
            {studentSubject.subject.name.charAt(0)}
          </span>
          <span className="subject-list__copy">
            <strong>{studentSubject.subject.name}</strong>
            <small>
              {studentSubject.subject.is_active === false
                ? 'Retired from the current catalogue'
                : studentSubject.subject.category}
            </small>
          </span>
          <button
            type="button"
            onClick={() => {
              if (window.confirm(`Archive ${studentSubject.subject.name}? Its existing grade history will be preserved.`)) {
                onRemove(studentSubject)
              }
            }}
            disabled={disabled}
            className="subject-list__remove"
            aria-label={`Archive ${studentSubject.subject.name}`}
          >
            ×
          </button>
        </li>
      ))}
    </ul>
  )
}
