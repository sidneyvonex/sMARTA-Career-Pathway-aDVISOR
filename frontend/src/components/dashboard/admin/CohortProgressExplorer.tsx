import { useMemo, useState } from 'react'
import type { SchoolProgressAggregate } from '../../../api/schoolAdmin'

interface Props {
  records: SchoolProgressAggregate[]
}

const BAND = {
  below: '#c24b3a',
  approaching: '#d58b00',
  meeting: '#247a62',
  exceeding: '#173f73',
}

function bandFor(level: string) {
  if (level.startsWith('EE')) return 'exceeding'
  if (level.startsWith('ME')) return 'meeting'
  if (level.startsWith('AE')) return 'approaching'
  return 'below'
}

export default function CohortProgressExplorer({ records }: Props) {
  const [year, setYear] = useState('all')
  const [subject, setSubject] = useState('all')
  const years = Array.from(new Set(records.map((record) => record.year))).sort((a, b) => b - a)
  const subjects = Array.from(new Map(
    records.map((record) => [record.continuity_code, record.subject_name]),
  ).entries()).sort((a, b) => a[1].localeCompare(b[1]))

  const filtered = records.filter((record) => (
    (year === 'all' || record.year === Number(year))
    && (subject === 'all' || record.continuity_code === subject)
  ))
  const chartData = useMemo(() => [1, 2, 3].map((term) => {
    const row: Record<string, string | number> = { term: `Term ${term}` }
    Object.keys(BAND).forEach((band) => { row[band] = 0 })
    filtered.filter((record) => record.term === term).forEach((record) => {
      const band = bandFor(record.level)
      row[band] = Number(row[band]) + record.count
    })
    return row
  }), [filtered])
  const totalEvidence = filtered.reduce((total, record) => total + record.count, 0)
  const meetingOrAbove = filtered
    .filter((record) => ['meeting', 'exceeding'].includes(bandFor(record.level)))
    .reduce((total, record) => total + record.count, 0)
  const chartMaximum = Math.max(...chartData.map((item) => (
    Number(item.below) + Number(item.approaching) + Number(item.meeting) + Number(item.exceeding)
  )), 1)

  return (
    <section className="db-panel cohort-progress" aria-labelledby="cohort-progress-title">
      <div className="cohort-progress__heading">
        <div>
          <p className="cohort-progress__eyebrow">Academic evidence</p>
          <h2 id="cohort-progress-title">Cohort progress by term</h2>
          <p>Aggregated CBC bands support planning without exposing individual learner results.</p>
        </div>
        <div className="cohort-progress__filters" aria-label="Filter cohort academic progress">
          <label>
            Cohort academic year
            <select value={year} onChange={(event) => setYear(event.target.value)}>
              <option value="all">All years</option>
              {years.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          <label>
            Cohort subject
            <select value={subject} onChange={(event) => setSubject(event.target.value)}>
              <option value="all">All subjects</option>
              {subjects.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
            </select>
          </label>
        </div>
      </div>

      {totalEvidence ? (
        <>
          <div className="cohort-progress__summary" aria-label="Cohort progress summary">
            <div><span>Evidence records</span><strong>{totalEvidence}</strong></div>
            <div><span>Meeting or above</span><strong>{meetingOrAbove}</strong></div>
            <div><span>Subjects represented</span><strong>{new Set(filtered.map((record) => record.continuity_code)).size}</strong></div>
          </div>
          <div className="cohort-progress__chart" role="img" aria-label="Stacked bar chart of cohort CBC bands by term">
            <svg viewBox="0 0 900 320" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
              {[0, 0.5, 1].map((ratio) => {
                const y = 260 - ratio * 220
                return (
                  <g key={ratio}>
                    <line x1="70" y1={y} x2="690" y2={y} className="cohort-progress__gridline" />
                    <text x="58" y={y + 4} textAnchor="end">{Math.round(chartMaximum * ratio)}</text>
                  </g>
                )
              })}
              {chartData.map((item, index) => {
                const x = 130 + index * 190
                let y = 260
                const segments = (Object.keys(BAND) as Array<keyof typeof BAND>).map((band) => {
                  const height = Number(item[band]) / chartMaximum * 220
                  y -= height
                  return <rect key={band} x={x} y={y} width="100" height={height} fill={BAND[band]} />
                })
                return (
                  <g key={String(item.term)}>
                    {segments}
                    <text x={x + 50} y="288" textAnchor="middle">{item.term}</text>
                  </g>
                )
              })}
              {(Object.keys(BAND) as Array<keyof typeof BAND>).reverse().map((band, index) => (
                <g key={band}>
                  <rect x="735" y={55 + index * 42} width="18" height="18" fill={BAND[band]} />
                  <text x="765" y={69 + index * 42}>{`${band.charAt(0).toUpperCase()}${band.slice(1)} expectation`}</text>
                </g>
              ))}
            </svg>
          </div>
        </>
      ) : (
        <p className="school-operations__empty">No academic evidence matches these filters yet.</p>
      )}
    </section>
  )
}
