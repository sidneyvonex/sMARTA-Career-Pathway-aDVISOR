import type { AssessmentRecommendation } from '../../api/assessment'

interface Props {
  recommendations: AssessmentRecommendation[]
  hollandCode: string
}

export default function RecommendationCards({ recommendations, hollandCode }: Props) {
  return (
    <div>
      <div className="results-holland-code">
        <div className="results-holland-badge" aria-label={`Holland Code: ${hollandCode}`}>
          {hollandCode}
        </div>
        <p style={{ marginTop: '0.5rem', color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
          Your Holland Code
        </p>
      </div>

      <div className="recommendation-cards">
        {recommendations.map((rec) => (
          <div
            key={rec.rank}
            className={`recommendation-card rank-${rec.rank}`}
            role="article"
            aria-label={`Rank ${rec.rank}: ${rec.pathway.name}`}
          >
            <div className="recommendation-header">
              <div className="recommendation-rank" aria-hidden="true">
                {rec.rank}
              </div>
              <span className="recommendation-name">{rec.pathway.name}</span>
            </div>
            <div
              className="recommendation-fit-bar"
              role="progressbar"
              aria-valuenow={rec.fit_pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Fit: ${rec.fit_pct}%`}
            >
              <div
                className="recommendation-fit-fill"
                style={{ width: `${rec.fit_pct}%` }}
              />
            </div>
            <p className="recommendation-fit-pct">{rec.fit_pct}% match</p>
            <p className="recommendation-description">{rec.pathway.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
