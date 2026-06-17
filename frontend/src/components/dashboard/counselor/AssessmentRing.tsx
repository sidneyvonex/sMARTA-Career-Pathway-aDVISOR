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
        <circle cx="65" cy="65" r={r} fill="none" stroke="var(--color-border)" strokeWidth="14" />
        <circle
          cx="65" cy="65" r={r}
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="14"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 65 65)"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text x="65" y="60" textAnchor="middle" style={{ fontSize: '1.4rem', fontWeight: 700, fill: 'var(--color-primary)' }}>
          {pct}%
        </text>
        <text x="65" y="78" textAnchor="middle" style={{ fontSize: '0.7rem', fill: 'var(--color-text-secondary)' }}>
          complete
        </text>
      </svg>

      <div className="ring-legend">
        <div className="ring-legend__item">
          <span className="ring-legend__dot" style={{ background: 'var(--color-primary)' }} />
          Assessed ({done})
        </div>
        <div className="ring-legend__item">
          <span className="ring-legend__dot" style={{ background: 'var(--color-border)' }} />
          Pending ({total - done})
        </div>
      </div>
    </div>
  )
}
