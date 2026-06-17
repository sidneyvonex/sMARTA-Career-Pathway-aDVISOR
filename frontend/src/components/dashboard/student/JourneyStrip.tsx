const CHECK_ICON = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
)

const DOT_ICON = (
  <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor" aria-hidden="true">
    <circle cx="4" cy="4" r="4" />
  </svg>
)

type StepState = 'done' | 'active' | 'todo'

interface Step {
  label: string
}

const STEPS: Step[] = [
  { label: 'Created account' },
  { label: 'Set up profile' },
  { label: 'Added subjects' },
  { label: 'Took career quiz' },
  { label: 'Explore results' },
  { label: 'Talk to counselor' },
]

interface Props {
  profileComplete: boolean
  subjectCount: number
  quizDone: boolean
  counselorAssigned: boolean
}

function stepState(index: number, props: Props): StepState {
  const completions = [
    true,
    props.profileComplete,
    props.subjectCount > 0,
    props.quizDone,
    props.quizDone,
    props.counselorAssigned,
  ]
  if (completions[index]) return 'done'
  const firstIncomplete = completions.findIndex((c) => !c)
  if (firstIncomplete === index) return 'active'
  return 'todo'
}

export default function JourneyStrip(props: Props) {
  return (
    <div className="journey-strip" role="region" aria-label="Your journey">
      <p className="dashboard-card__title" style={{ marginBottom: 'var(--space-4)' }}>
        Your journey
      </p>
      <div className="journey-strip__steps">
        {STEPS.map((step, i) => {
          const state = stepState(i, props)
          return (
            <div
              key={step.label}
              className={`journey-step journey-step--${state}`}
              aria-label={`${step.label}: ${state}`}
            >
              <div className={`journey-dot journey-dot--${state}`}>
                {state === 'done' ? CHECK_ICON : state === 'active' ? DOT_ICON : i + 1}
              </div>
              <span className="journey-step__label">{step.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
