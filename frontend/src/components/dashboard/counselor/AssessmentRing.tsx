interface Props {
  done: number
  total: number
}

export default function AssessmentRing({ done, total }: Props) {
  const pct = total === 0 ? 0 : Math.round((done / total) * 100)
  const r = 54
  const circumference = 2 * Math.PI * r
  const offset = circumference * (1 - pct / 100)

  return (
    <div className="assessment-ring-card">
      <svg width="130" height="130" viewBox="0 0 130 130" role="img" aria-label={`${pct}% assessments complete`}>
        <circle className="assessment-ring__track" cx="65" cy="65" r={r} fill="none" strokeWidth="14" />
        <circle
          cx="65" cy="65" r={r}
          fill="none"
          className="assessment-ring__value"
          strokeWidth="14"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 65 65)"
        />
        <text className="assessment-ring__percent" x="65" y="60" textAnchor="middle">
          {pct}%
        </text>
        <text className="assessment-ring__label" x="65" y="78" textAnchor="middle">
          complete
        </text>
      </svg>

      <div className="ring-legend">
        <div className="ring-legend__item">
          <span className="ring-legend__dot ring-legend__dot--done" />
          Assessed ({done})
        </div>
        <div className="ring-legend__item">
          <span className="ring-legend__dot ring-legend__dot--pending" />
          Pending ({total - done})
        </div>
      </div>
    </div>
  )
}
