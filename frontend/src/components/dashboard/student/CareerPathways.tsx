import type { AssessmentResult } from '../../../api/assessment'

interface Props {
  result: AssessmentResult
}

export default function CareerPathways({ result }: Props) {
  const recs = result.recommendations.slice(0, 3)

  return (
    <div className="dashboard-card">
      <p className="dashboard-card__title">Best careers for you</p>
      <div className="career-pathways">
        {recs.map((rec) => (
          <div
            key={rec.rank}
            className={`pathway-item${rec.rank === 1 ? ' pathway-item--first' : ''}`}
          >
            <div className="pathway-item__header">
              <span className="pathway-item__rank">{rec.rank}</span>
              <span className="pathway-item__name">{rec.pathway.name}</span>
              {rec.rank === 1 && <span className="best-fit-badge">Best fit</span>}
              <span className="pathway-item__pct">{rec.fit_pct}%</span>
            </div>
            <div className="pathway-item__track">
              <div className="pathway-item__fill" style={{ width: `${rec.fit_pct}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
