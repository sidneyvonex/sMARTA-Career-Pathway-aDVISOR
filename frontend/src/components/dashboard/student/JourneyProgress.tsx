interface Props {
  profileComplete: boolean
  hasSubjects: boolean
  quizDone: boolean
  counselorAssigned: boolean
}

const STEP_LABELS = [
  'Account created',
  'Profile set up',
  'Subjects added',
  'Quiz taken',
  'Results explored',
  'Counselor connected',
]

export default function JourneyProgress(props: Props) {
  const completions = [
    true,
    props.profileComplete,
    props.hasSubjects,
    props.quizDone,
    props.quizDone,
    props.counselorAssigned,
  ]

  const doneCount = completions.filter(Boolean).length
  const activeIndex = completions.findIndex((c) => !c)

  return (
    <div className="journey-bar" role="progressbar" aria-valuenow={doneCount} aria-valuemin={0} aria-valuemax={6} aria-label="Journey progress">
      <div className="journey-bar__dots">
        {completions.map((done, i) => (
          <div
            key={i}
            className={`journey-bar__dot${done ? ' journey-bar__dot--done' : i === activeIndex ? ' journey-bar__dot--active' : ''}`}
            title={STEP_LABELS[i]}
          />
        ))}
      </div>
      <span className="journey-bar__label">Step {Math.min(doneCount + 1, 6)} of 6</span>
    </div>
  )
}
