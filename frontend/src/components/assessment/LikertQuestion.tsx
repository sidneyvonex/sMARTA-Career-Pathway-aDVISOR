import { LIKERT_LABELS } from '../../api/assessment'
import type { RIASECQuestion } from '../../api/assessment'

interface Props {
  question: RIASECQuestion
  questionNumber: number
  value: number | undefined
  onChange: (questionId: number, score: number) => void
}

export default function LikertQuestion({ question, questionNumber, value, onChange }: Props) {
  return (
    <div className="likert-question">
      <p className="likert-text">
        <span style={{ color: 'var(--color-text-secondary)', marginRight: '0.5rem' }}>
          {questionNumber}.
        </span>
        {question.text}
      </p>
      <div className="likert-options" role="group" aria-label={`Response for: ${question.text}`}>
        {[1, 2, 3, 4, 5].map((score) => (
          <button
            key={score}
            type="button"
            className={`likert-btn${value === score ? ' selected' : ''}`}
            onClick={() => onChange(question.id, score)}
            aria-pressed={value === score}
            aria-label={LIKERT_LABELS[score]}
          >
            <span className="likert-btn-number">{score}</span>
            <span className="likert-btn-label">{LIKERT_LABELS[score]}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
