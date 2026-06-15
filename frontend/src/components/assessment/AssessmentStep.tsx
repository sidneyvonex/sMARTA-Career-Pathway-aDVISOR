import LikertQuestion from './LikertQuestion'
import type { RIASECQuestion } from '../../api/assessment'

interface Props {
  questions: RIASECQuestion[]
  pageIndex: number
  answers: Record<number, number>
  onAnswer: (questionId: number, score: number) => void
}

export default function AssessmentStep({ questions, pageIndex, answers, onAnswer }: Props) {
  const startNumber = pageIndex * 6 + 1
  return (
    <div>
      {questions.map((q, i) => (
        <LikertQuestion
          key={q.id}
          question={q}
          questionNumber={startNumber + i}
          value={answers[q.id]}
          onChange={onAnswer}
        />
      ))}
    </div>
  )
}
