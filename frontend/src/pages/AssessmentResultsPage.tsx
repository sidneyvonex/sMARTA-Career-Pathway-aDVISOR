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
    return (
      <div className="assessment-page">
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading your results…</p>
      </div>
    )
  }

  if (isError || !data?.data.data) {
    return (
      <div className="assessment-page">
        <div className="assessment-card" style={{ textAlign: 'center' }}>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
            No assessment results found.
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={() => navigate('/assessment')}
            style={{ minHeight: 'var(--min-touch-target, 44px)' }}
          >
            Take the Assessment
          </button>
        </div>
      </div>
    )
  }

  const result = data.data.data

  return (
    <div className="assessment-page">
      <div className="assessment-card">
        <h1 style={{
          fontSize: 'var(--font-size-xl, 1.25rem)',
          fontWeight: 700,
          color: 'var(--color-text)',
          marginBottom: 'var(--space-6, 1.5rem)',
          textAlign: 'center',
        }}>
          Your Results
        </h1>

        <RecommendationCards
          recommendations={result.recommendations}
          hollandCode={result.holland_code}
        />

        <hr style={{ border: 'none', borderTop: '1px solid var(--color-border, #e5e7eb)', margin: 'var(--space-6, 1.5rem) 0' }} />

        <h2 style={{
          fontSize: 'var(--font-size-base, 1rem)',
          fontWeight: 700,
          color: 'var(--color-text)',
          marginBottom: 'var(--space-4, 1rem)',
        }}>
          Your Dimension Scores
        </h2>
        <ScoreBars scores={result.scores} />

        <div style={{ marginTop: 'var(--space-6, 1.5rem)', display: 'flex', gap: 'var(--space-3, 0.75rem)', justifyContent: 'center' }}>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => navigate('/assessment')}
          >
            Retake Assessment
          </button>
        </div>
      </div>
    </div>
  )
}
