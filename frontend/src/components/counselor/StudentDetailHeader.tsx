import { initials } from '../../lib/format'
import type { StudentDetail } from '../../api/counselor'

interface Props {
  student: StudentDetail['student']
}

export default function StudentDetailHeader({ student }: Props) {
  return (
    <div className="detail-header">
      <div className="detail-header__avatar" aria-hidden="true">
        {student.photo_url ? (
          <img
            src={student.photo_url}
            alt=""
            className="detail-header__photo"
          />
        ) : (
          initials(student.first_name, student.last_name)
        )}
      </div>

      <div className="detail-header__info">
        <h1 className="detail-header__name">
          {student.first_name} {student.last_name}
        </h1>

        <div className="detail-header__meta">
          <span className="detail-header__badge">Grade {student.grade}</span>
          {student.county && (
            <span className="detail-header__meta-item">{student.county}</span>
          )}
          {student.school && (
            <span className="detail-header__meta-item">{student.school}</span>
          )}
        </div>

        {student.bio && (
          <p className="detail-header__bio">{student.bio}</p>
        )}
      </div>
    </div>
  )
}
