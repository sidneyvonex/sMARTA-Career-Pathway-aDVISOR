const STEPS = [
  {
    number: '01',
    tone: 'flame' as const,
    tag: 'Start here',
    title: 'Discover',
    body: 'Take the 15-minute RIASEC interest assessment — free, no wrong answers.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="9" />
        <path d="M14.5 9.5L12 12l-2.5 2.5L12 12l2.5-2.5z" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    number: '02',
    tone: 'forest' as const,
    tag: 'Automatic',
    title: 'Plan',
    body: 'Get matched to a CBC pathway, ranked by how you actually scored.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6z" />
        <path d="M9 4v14M15 6v14" />
      </svg>
    ),
  },
  {
    number: '03',
    tone: 'forest' as const,
    tag: 'Your choice',
    title: 'Choose',
    body: 'Pick your subjects with a clear view of where each pathway leads.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <path d="M8 12l3 3 5-6" />
      </svg>
    ),
  },
  {
    number: '04',
    tone: 'flame' as const,
    tag: 'Every term',
    title: 'Succeed',
    body: 'Track your grades every term and watch your pathway fit update in real time.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 17l6-6 4 4 8-8" />
        <path d="M17 7h4v4" />
      </svg>
    ),
  },
]

export default function LandingSteps() {
  return (
    <section className="landing-section" id="how-it-works">
      <span className="landing-eyebrow">How it works</span>
      <h2 className="landing-section__heading" style={{ marginTop: '0.75rem' }}>
        Four steps. One school year.
      </h2>

      <div className="landing-step-grid">
        {STEPS.map((step, index) => (
          <div
            className={`landing-step-tile${index === 1 || index === 2 ? ' landing-step-tile--alt' : ''}`}
            key={step.title}
          >
            <span className="landing-step-tile__number">{step.number}</span>
            <span className={`landing-step-tile__icon landing-step-tile__icon--${step.tone}`}>
              {step.icon}
            </span>
            <span className="landing-step-tile__tag">{step.tag}</span>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
