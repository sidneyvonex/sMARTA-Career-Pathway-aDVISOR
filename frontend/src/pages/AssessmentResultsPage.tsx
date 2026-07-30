import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ScoreBars from '../components/assessment/ScoreBars'
import RecommendationCards from '../components/assessment/RecommendationCards'
import { assessmentApi } from '../api/assessment'
import '../styles/assessment.css'

export default function AssessmentResultsPage() {
  const navigate = useNavigate()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['assessment-latest'],
    queryFn: () => assessmentApi.getLatest(),
  })

  if (isLoading) {
    return <div className="assessment-state">Building your career profile…</div>
  }

  if (isError || !data?.data.data) {
    return (
      <div className="assessment-page assessment-page--results">
        <div className="assessment-empty">
          <span aria-hidden="true">✦</span>
          <h1>Your career profile starts here</h1>
          <p>Complete the quiz to reveal your interest shape and best-fit CBC pathways.</p>
          <button type="button" className="assessment-button" onClick={() => navigate('/assessment')}>
            Take the Assessment
          </button>
        </div>
      </div>
    )
  }

  const result = data.data.data
  const topMatch = result.recommendations[0]

  return (
    <div className="assessment-page assessment-page--results">
      <header className="results-hero">
        <div>
          <span className="assessment-eyebrow">Your career profile</span>
          <h1>Your interests have a shape.</h1>
          <p>
            {topMatch
              ? `${topMatch.pathway.name} is currently your strongest pathway match.`
              : 'Your RIASEC scores show the kinds of work and learning that may suit you.'}
          </p>
        </div>
        <div className="results-hero__code">
          <span>Holland code</span>
          <strong>{result.holland_code}</strong>
        </div>
      </header>

      <div className="results-layout">
        <section className="results-panel results-panel--matches">
          <div className="results-panel__heading">
            <div>
              <span className="assessment-eyebrow">Direction</span>
              <h2>Best-fit pathways</h2>
            </div>
            <span className="results-panel__spark" aria-hidden="true">✦</span>
          </div>
          <RecommendationCards
            recommendations={result.recommendations}
            hollandCode={result.holland_code}
            hideCode
          />
        </section>

        <section className="results-panel results-panel--scores">
          <div className="results-panel__heading">
            <div>
              <span className="assessment-eyebrow">Personality</span>
              <h2>Your dimension scores</h2>
            </div>
          </div>
          <p className="results-panel__intro">These six dimensions combine to form your personal interest pattern.</p>
          <ScoreBars scores={result.scores} />
          <button
            type="button"
            className="assessment-button assessment-button--secondary assessment-button--wide"
            onClick={() => navigate('/assessment')}
          >
            Retake assessment
          </button>
        </section>
      </div>
    </div>
  )
}
