import { CBCGrade, GRADE_LEVEL_LABELS } from '../../api/students'

interface Props {
  grades: CBCGrade[]
}

export default function GradeHistory({ grades }: Props) {
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
          </tr>
        </thead>
        <tbody>
          {grades.map((grade) => (
            <tr key={grade.id}>
              <td>Term {grade.term}</td>
              <td>{grade.year}</td>
              <td>
                <span className={`grade-level grade-level--${grade.level.slice(0, 2).toLowerCase()}`}>
                  {GRADE_LEVEL_LABELS[grade.level]}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
