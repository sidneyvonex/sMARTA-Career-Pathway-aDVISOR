import { DIMENSION_LABELS } from '../../api/assessment'
import type { RIASECDimension } from '../../api/assessment'

interface Props {
  scores: Record<RIASECDimension, number>
}

const DIM_ORDER: RIASECDimension[] = ['R', 'I', 'A', 'S', 'E', 'C']
const MAX_SCORE = 25

export default function ScoreBars({ scores }: Props) {
  return (
    <div className="score-bars">
      {DIM_ORDER.map((dim) => {
        const score = scores[dim] ?? 0
        const pct = Math.round((score / MAX_SCORE) * 100)
        return (
          <div key={dim} className="score-bar-row">
            <span className="score-bar-label">{DIMENSION_LABELS[dim]}</span>
            <div className="score-bar-track" aria-hidden="true">
              <div className="score-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="score-bar-value" aria-label={`${score} out of ${MAX_SCORE}`}>
              {score}
            </span>
          </div>
        )
      })}
    </div>
  )
}
