import type { AssessmentResult, RIASECDimension } from '../../../api/assessment'

const TRAIT_INFO: Record<RIASECDimension, { name: string; description: string }> = {
  R: { name: 'Hands-on', description: 'You enjoy working with tools, machines, or the outdoors.' },
  I: { name: 'Curious', description: 'You love investigating ideas, solving problems, and researching.' },
  A: { name: 'Creative', description: 'You express yourself through art, design, music, or writing.' },
  S: { name: 'Social', description: 'You enjoy helping, teaching, or working closely with people.' },
  E: { name: 'Ambitious', description: 'You like leading others, making decisions, and taking initiative.' },
  C: { name: 'Organised', description: 'You prefer structured tasks, data, and clear procedures.' },
}

const MAX_SCORE = 25

interface Props {
  result: AssessmentResult
}

export default function TraitBars({ result }: Props) {
  const sorted = (Object.keys(result.scores) as RIASECDimension[]).sort(
    (a, b) => result.scores[b] - result.scores[a],
  )

  return (
    <div className="dashboard-card">
      <p className="dashboard-card__title">How you see the world</p>
      <div className="trait-bars">
        {sorted.map((dim, i) => {
          const pct = Math.round((result.scores[dim] / MAX_SCORE) * 100)
          const fillClass =
            i < 2 ? 'trait-bar__fill--top'
            : i < 4 ? 'trait-bar__fill--mid'
            : 'trait-bar__fill--low'
          const { name, description } = TRAIT_INFO[dim]

          return (
            <div key={dim} className="trait-bar">
              <div className="trait-bar__header">
                <div>
                  <div className="trait-bar__name">{name}</div>
                  <div className="trait-bar__desc">{description}</div>
                </div>
                <span className="trait-bar__pct">{pct}%</span>
              </div>
              <div className="trait-bar__track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={name}>
                <div className={`trait-bar__fill ${fillClass}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
