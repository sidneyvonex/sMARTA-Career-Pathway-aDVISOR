import { GRADE_LEVEL_LABELS, type GradeLevel } from '../../api/students'
import type { StudentDetail } from '../../api/counselor'

interface Props {
  grades: StudentDetail['grades']
  studentName: string
}

export default function CounselorGradesTable({ grades, studentName }: Props) {
  if (grades.length === 0) {
    return (
      <div className="grades-table-wrap">
        <div className="table-empty">
          {studentName} hasn&rsquo;t entered any grades yet.
        </div>
      </div>
    )
  }

  return (
    <div className="grades-table-wrap">
      <table className="grades-table">
        <thead>
          <tr>
            <th>Subject</th>
            <th>Code</th>
            <th>Term</th>
            <th>Year</th>
            <th>Level</th>
          </tr>
        </thead>
        <tbody>
          {grades.map((g) => (
            <tr key={g.id}>
              <td>{g.subject_name}</td>
              <td>{g.subject_code}</td>
              <td>Term {g.term}</td>
              <td>{g.year}</td>
              <td className="grades-table__level">
                {GRADE_LEVEL_LABELS[g.level as GradeLevel] ?? g.level}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
