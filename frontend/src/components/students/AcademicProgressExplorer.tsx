import { useMemo, useState } from 'react'
import {
  GRADE_LEVEL_LABELS,
  GRADE_LEVEL_POINTS,
  type ProgressAssessment,
  type ProgressEvidence,
} from '../../api/students'
import './AcademicProgressExplorer.css'

export interface AcademicProgressFilters {
  year?: number
  term?: 1 | 2 | 3
  subject?: string
  academic?: boolean
}

interface Props {
  progress: ProgressAssessment
  heading?: string
  description?: string
  onDownload?: (filters: AcademicProgressFilters) => void
  downloading?: boolean
}

const SERIES = ['#136f63', '#1769aa', '#d58b00', '#7b4ab5', '#c24949', '#217a9b']
const DASHES = [undefined, '8 4', '3 3', '10 3 2 3', '2 5', '12 4']

function periodKey(record: ProgressEvidence) {
  return `${record.year}-${record.term}`
}

function bandLabel(points: number) {
  if (points >= 7) return 'Exceeding'
  if (points >= 5) return 'Meeting'
  if (points >= 3) return 'Approaching'
  return 'Below'
}

export default function AcademicProgressExplorer({
  progress,
  heading = 'Progress across terms',
  description = 'Compare CBC performance bands across terms and subjects. Filters also apply to the downloaded report.',
  onDownload,
  downloading = false,
}: Props) {
  const [year, setYear] = useState('all')
  const [term, setTerm] = useState('all')
  const [subject, setSubject] = useState('all')

  const subjects = progress.subjects
  const years = useMemo(() => Array.from(new Set(
    subjects.flatMap((item) => item.evidence.map((record) => record.year)),
  )).sort((a, b) => b - a), [subjects])

  const visibleSubjects = useMemo(() => subjects.flatMap((item) => {
    if (subject !== 'all' && item.continuity_code !== subject) return []
    const evidence = item.evidence.filter((record) => (
      (year === 'all' || record.year === Number(year))
      && (term === 'all' || record.term === Number(term))
    ))
    return evidence.length ? [{ ...item, evidence }] : []
  }), [subjects, subject, term, year])

  const periods = useMemo(() => Array.from(new Map(
    visibleSubjects.flatMap((item) => item.evidence).map((record) => [periodKey(record), record]),
  ).values()).sort((a, b) => a.year - b.year || a.term - b.term), [visibleSubjects])

  const chartData = periods.map((period) => {
    const point: Record<string, string | number | null> = {
      period: years.length > 1 ? `${period.year} T${period.term}` : `Term ${period.term}`,
    }
    visibleSubjects.forEach((item) => {
      const record = item.evidence.find((candidate) => periodKey(candidate) === periodKey(period))
      point[item.continuity_code] = record ? GRADE_LEVEL_POINTS[record.level] : null
    })
    return point
  })

  const improving = visibleSubjects.filter((item) => {
    const ordered = [...item.evidence].sort((a, b) => a.year - b.year || a.term - b.term)
    if (ordered.length < 2) return false
    return GRADE_LEVEL_POINTS[ordered[ordered.length - 1].level] > GRADE_LEVEL_POINTS[ordered[0].level]
  }).length
  const evidenceCount = visibleSubjects.reduce((total, item) => total + item.evidence.length, 0)
  const latestRecords = visibleSubjects.flatMap((item) => (
    [...item.evidence].sort((a, b) => b.year - a.year || b.term - a.term).slice(0, 1)
  ))
  const meetingOrAbove = latestRecords.filter((record) => GRADE_LEVEL_POINTS[record.level] >= 5).length
  const filters: AcademicProgressFilters = {
    year: year === 'all' ? undefined : Number(year),
    term: term === 'all' ? undefined : Number(term) as 1 | 2 | 3,
    subject: subject === 'all' ? undefined : subject,
  }

  return (
    <section className="progress-explorer" aria-labelledby="progress-explorer-title">
      <div className="progress-section-heading progress-explorer__heading">
        <div>
          <h2 id="progress-explorer-title">{heading}</h2>
          <p>{description}</p>
        </div>
        {onDownload && (
          <button
            type="button"
            className="student-action student-action--primary"
            onClick={() => onDownload({ ...filters, academic: true })}
            disabled={downloading}
          >
            {downloading ? 'Preparing report...' : 'Download filtered report'}
          </button>
        )}
      </div>

      <div className="progress-explorer__filters" aria-label="Filter academic progress">
        <label>
          Report academic year
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            <option value="all">All years</option>
            {years.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Report term
          <select value={term} onChange={(event) => setTerm(event.target.value)}>
            <option value="all">All terms</option>
            {[1, 2, 3].map((value) => <option key={value} value={value}>Term {value}</option>)}
          </select>
        </label>
        <label>
          Report subject
          <select value={subject} onChange={(event) => setSubject(event.target.value)}>
            <option value="all">All subjects</option>
            {subjects.map((item) => (
              <option key={item.continuity_code} value={item.continuity_code}>{item.subject_name}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="progress-explorer__metrics" aria-label="Filtered academic progress summary">
        <div><span>Subjects shown</span><strong>{visibleSubjects.length}</strong></div>
        <div><span>Improving</span><strong>{improving}</strong></div>
        <div><span>Meeting or above</span><strong>{meetingOrAbove} of {latestRecords.length}</strong></div>
        <div><span>Evidence records</span><strong>{evidenceCount}</strong></div>
      </div>

      {chartData.length ? (
        <>
          <div className="progress-explorer__legend" aria-label="Chart subjects">
            {visibleSubjects.map((item, index) => (
              <span key={item.continuity_code}>
                <i
                  aria-hidden="true"
                  style={{
                    backgroundColor: SERIES[index % SERIES.length],
                    backgroundImage: DASHES[index % DASHES.length]
                      ? `repeating-linear-gradient(90deg, transparent 0 5px, var(--color-surface) 5px 8px)`
                      : undefined,
                  }}
                />
                {item.subject_name}
              </span>
            ))}
          </div>

          <div className="progress-explorer__chart" role="img" aria-label="Line chart of CBC performance bands by academic term and subject">
            <svg viewBox="0 0 760 320" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
              {[1, 3, 5, 7].map((points) => {
                const y = 260 - ((points - 1) / 7) * 210
                return (
                  <g key={points}>
                    <line x1="120" y1={y} x2="720" y2={y} className="progress-explorer__gridline" />
                    <text x="108" y={y + 4} textAnchor="end">{bandLabel(points)}</text>
                  </g>
                )
              })}
              {chartData.map((point, index) => {
                const x = chartData.length === 1 ? 420 : 140 + index * (560 / (chartData.length - 1))
                return <text key={String(point.period)} x={x} y="290" textAnchor="middle">{point.period}</text>
              })}
              {visibleSubjects.map((item, index) => {
                const points = chartData.flatMap((point, pointIndex) => {
                  const value = point[item.continuity_code]
                  if (typeof value !== 'number') return []
                  const x = chartData.length === 1 ? 420 : 140 + pointIndex * (560 / (chartData.length - 1))
                  const y = 260 - ((value - 1) / 7) * 210
                  return [{ x, y }]
                })
                const color = SERIES[index % SERIES.length]
                return (
                  <g key={item.continuity_code}>
                    {points.length > 1 && (
                      <polyline
                        points={points.map((point) => `${point.x},${point.y}`).join(' ')}
                        fill="none"
                        stroke={color}
                        strokeDasharray={DASHES[index % DASHES.length]}
                        strokeWidth="3"
                      />
                    )}
                    {points.map((point, pointIndex) => <circle key={pointIndex} cx={point.x} cy={point.y} r="5" fill={color} />)}
                  </g>
                )
              })}
            </svg>
          </div>

          <div className="progress-explorer__table-wrap">
            <table aria-label="Academic progress by subject and term">
              <thead><tr><th>Subject</th><th>Period</th><th>CBC band</th><th>Evidence</th><th>Verification</th></tr></thead>
              <tbody>
                {visibleSubjects.flatMap((item) => item.evidence.map((record) => (
                  <tr key={`${item.continuity_code}-${record.id}`}>
                    <th scope="row" data-label="Subject">{item.subject_name}</th>
                    <td data-label="Period">{record.year}, Term {record.term}</td>
                    <td data-label="CBC band"><strong className="progress-explorer__band">{GRADE_LEVEL_LABELS[record.level]}</strong></td>
                    <td data-label="Evidence">{record.source === 'school' ? 'School entered' : 'Learner entered'}</td>
                    <td data-label="Verification">
                      <span className={`progress-explorer__verification${record.verified_at ? ' is-verified' : ''}`}>
                        {record.verified_at ? 'School verified' : 'Not school verified'}
                      </span>
                    </td>
                  </tr>
                ))) }
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="progress-explorer__empty">No academic evidence matches these filters.</p>
      )}
    </section>
  )
}
