import { Link } from 'react-router-dom'
import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import '../styles/marketing.css'

type Step = {
  number: string
  icon: 'flame' | 'forest'
  tag: string
  title: string
  body: string
  alt?: boolean
}

const STEPS: Step[] = [
  {
    number: '01',
    icon: 'flame',
    tag: '~15 minutes',
    title: 'Discover',
    body: 'Take the RIASEC interest assessment: 24 short statements, rated on how much they sound like you. No wrong answers, no time pressure.',
  },
  {
    number: '02',
    icon: 'forest',
    tag: 'Automatic',
    title: 'Plan',
    body: "Your responses are scored across all 6 RIASEC dimensions, then matched against each CBC pathway's profile — ranked by fit, not a single verdict.",
    alt: true,
  },
  {
    number: '03',
    icon: 'forest',
    tag: 'Your choice',
    title: 'Choose',
    body: 'See exactly which subjects sit inside each pathway before you commit — Pure Sciences and Technical Studies under STEM, Languages and Humanities under Social Sciences, and so on.',
    alt: true,
  },
  {
    number: '04',
    icon: 'flame',
    tag: 'Every term',
    title: 'Succeed',
    body: 'Log your grades every term. Your teacher, counselor, and — if your school enables it — your parent can see the same picture you do.',
  },
]

const DIMENSIONS = [
  { letter: 'R', title: 'Realistic', body: 'Hands-on and practical — building, fixing, working with tools or outdoors.' },
  { letter: 'I', title: 'Investigative', body: 'Curious and analytical — asking why, testing ideas, solving problems.' },
  { letter: 'A', title: 'Artistic', body: 'Expressive and original — music, art, design, performance.' },
  { letter: 'S', title: 'Social', body: 'People-focused — teaching, helping, guiding, listening.' },
  { letter: 'E', title: 'Enterprising', body: 'Persuasive and driven — leading, organizing, taking initiative.' },
  { letter: 'C', title: 'Conventional', body: 'Structured and detail-oriented — organizing data, following procedure.' },
]

const FAQS = [
  {
    question: 'Is the RIASEC model actually reliable?',
    answer:
      'RIASEC is a well-established framework used in career guidance worldwide. We use it as a strong starting point for a conversation about your interests — not a verdict carved in stone.',
  },
  {
    question: 'Can I retake the assessment?',
    answer:
      "Interests can shift, especially across Senior School. Retaking it is built in, and your history is kept so you can see how you've changed.",
  },
  {
    question: 'Who can see my results?',
    answer:
      'Your school counselor can see your results, to support you directly. Parents get visibility only where your school has enabled parent access.',
  },
  {
    question: "What if my top pathway isn't what I expected?",
    answer: "That's normal — and useful. It's a data point, not a decision. The final subject choice is always yours.",
  },
]

const STEP_ICONS: Record<Step['icon'], JSX.Element> = {
  flame: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M14.5 9.5L12 12l-2.5 2.5L12 12l2.5-2.5z" fill="currentColor" stroke="none" />
    </svg>
  ),
  forest: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
      <path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6z" />
      <path d="M9 4v14M15 6v14" />
    </svg>
  ),
}

export default function HowItWorksPage() {
  return (
    <div className="mk-how-it-works-page">
      <PublicNav />

      {/* HERO */}
      <section className="mk-hero">
        <div className="mk-hero__grid">
          <div>
            <span className="mk-eyebrow">The process</span>
            <h1 className="mk-hero__heading" style={{ marginTop: '1rem' }}>
              From confused
              <span className="mk-script">to confident.</span>
            </h1>
          </div>
          <div className="mk-hero__side">
            <p>Four steps, spread across a school year. No fees, no sales calls, no fine print.</p>
            <div className="mk-hero__ctas">
              <Link className="mk-btn mk-btn-dark" to="/register">Get Started</Link>
              <Link className="mk-btn mk-btn-outline" to="/pathways">See the pathways</Link>
            </div>
          </div>
        </div>
      </section>

      {/* BLACK BAND: STEPS */}
      <div className="mk-band mk-band--ink">
        <section className="mk-section">
          <span className="mk-eyebrow">The process</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>Four steps. One school year.</h2>

          <div className="mk-step-grid">
            {STEPS.map((step) => (
              <div className={`mk-step-tile${step.alt ? ' mk-step-tile--alt' : ''}`} key={step.number}>
                <span className="mk-step-tile__number">{step.number}</span>
                <span className={`mk-step-tile__icon mk-step-tile__icon--${step.icon}`}>
                  {STEP_ICONS[step.icon]}
                </span>
                <span className="mk-step-tile__tag">{step.tag}</span>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* GREEN BAND: RIASEC DIMENSIONS */}
      <div className="mk-band mk-band--green">
        <section className="mk-section" style={{ paddingTop: '4rem' }}>
          <span className="mk-eyebrow">Behind the assessment</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>The 6 RIASEC dimensions.</h2>
          <p className="mk-section__lede" style={{ marginTop: '1rem' }}>
            RIASEC — also called the Holland Code — is a well-established framework used in career guidance
            worldwide. Every question you answer scores against one of these six.
          </p>

          <div className="mk-dimension-grid">
            {DIMENSIONS.map((dimension) => (
              <div className="mk-dimension-card" key={dimension.letter}>
                <span className="mk-dimension-card__letter">{dimension.letter}</span>
                <h3>{dimension.title}</h3>
                <p>{dimension.body}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* FAQ */}
      <section className="mk-section mk-section--tight">
        <span className="mk-eyebrow">Questions</span>
        <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>Before you start.</h2>

        <div className="mk-faq">
          {FAQS.map((faq) => (
            <div className="mk-faq-item" key={faq.question}>
              <h3>{faq.question}</h3>
              <p>{faq.answer}</p>
            </div>
          ))}
        </div>
      </section>

      {/* GOLD BAND: CTA */}
      <div className="mk-band mk-band--gold">
        <section className="mk-section">
          <div className="mk-cta-band mk-cta-band--gold">
            <span className="mk-eyebrow">Last step</span>
            <p className="mk-cta-band__heading">
              Ready to see
              <span className="mk-script">where you actually fit?</span>
            </p>
            <p className="mk-cta-band__sub">Free forever. No credit card, ever.</p>
            <Link className="mk-btn mk-btn-dark" to="/register">
              Take the RIASEC Assessment
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
          </div>
        </section>
      </div>

      <PublicFooter />
    </div>
  )
}
