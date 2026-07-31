import type { AssessmentRecommendation } from '../../api/assessment'

interface Props {
  recommendations: AssessmentRecommendation[]
  hollandCode: string
  hideCode?: boolean
}

export default function RecommendationCards({ recommendations, hollandCode, hideCode = false }: Props) {
  return (
    <div>
      {!hideCode && <div className="results-holland-code">
        <div className="results-holland-badge" aria-label={`Holland Code: ${hollandCode}`}>
          {hollandCode}
        </div>
        <p>Your Holland Code</p>
      </div>}

      <p className="recommendation-advisory">
        These interest-aligned pathways are starting points for exploration. They do not predict
        success or decide placement; use them alongside your subjects, goals, opportunities, and
        guidance from a counsellor.
      </p>

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
            <p className="recommendation-fit-pct">
              {rec.rank === 1 ? 'Strongest interest alignment' : 'Suggested for exploration'}
            </p>
            <p className="recommendation-description">{rec.pathway.description}</p>
            {rec.explanation?.summary && (
              <p className="recommendation-explanation">{rec.explanation.summary}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
