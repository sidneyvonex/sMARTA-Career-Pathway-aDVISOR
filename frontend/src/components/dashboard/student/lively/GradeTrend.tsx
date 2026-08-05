import GradeSparkline from '../../../common/GradeSparkline'
import { GRADE_LEVEL_LABELS, type GradeLevel } from '../../../../api/students'

export interface GradeChronologyRecord {
  period: string
  level: GradeLevel
}

export interface GradeChronology {
  subject: string
  records: GradeChronologyRecord[]
}

export default function GradeTrend({ data }: { data: GradeChronology[] }) {
  return (
    <section className="lv-grade-chronology" role="region" aria-label="Academic evidence chronology">
      <p>Levels are shown within each subject and term.</p>
      <ul>
        {data.map((subject) => (
          <li key={subject.subject}>
            <div className="lv-grade-chronology__heading">
              <strong>{subject.subject}</strong>
              <GradeSparkline records={subject.records} />
            </div>
            <div>
              {subject.records.map((record) => (
                <span
                  key={`${record.period}-${record.level}`}
                  title={GRADE_LEVEL_LABELS[record.level]}
                >
                  {record.period} · {record.level}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
