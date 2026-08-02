import { Link } from 'react-router-dom'
import { hasSelectedPathway, type JourneyStatus } from '../../../api/students'

const ARROW = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
  </svg>
)

interface Step {
  title: string
  desc: string
  cta: string
  to: string
}

interface Flags {
  profileComplete: boolean
  journeyStatus: JourneyStatus
  hasSubjects: boolean
  quizDone: boolean
  counselorAssigned: boolean
}

function getNextStep(flags: Flags): Step {
  if (!flags.profileComplete) {
    return {
      title: 'Complete your profile',
      desc: 'Tell us about yourself — your grade, interests, and county — so we can suggest career paths to explore.',
      cta: 'Complete profile',
      to: '/profile',
    }
  }
  // Before we know where the learner is in their journey we cannot recommend a
  // sensible next step — ask them once.
  if (!flags.journeyStatus) {
    return {
      title: 'Tell us where you are',
      desc: 'Have you already chosen your Senior School pathway and subjects? Let us know so we can guide you the right way.',
      cta: 'Set my journey stage',
      to: '/profile',
    }
  }
  // Learners who already selected a pathway are here to track progress. RIASEC
  // is optional for them and never blocks progress tracking.
  if (hasSelectedPathway(flags.journeyStatus)) {
    if (!flags.hasSubjects) {
      return {
        title: 'Record your current subjects',
        desc: 'Add the subjects you already chose so we can track your progress and suggest improvement targets.',
        cta: 'Record subjects',
        to: '/grades',
      }
    }
    return {
      title: 'Track your progress',
      desc: 'Add your latest grades to see how each subject is trending and where a little support could help.',
      cta: 'View my progress',
      to: '/grades',
    }
  }
  if (flags.journeyStatus === 'reconsidering') {
    if (!flags.quizDone) {
      return {
        title: 'Reflect with the interest quiz',
        desc: 'Answer a few questions about what you enjoy. We\'ll show how your interests relate to your current pathway before you change anything.',
        cta: 'Start the quiz',
        to: '/assessment',
      }
    }
    return {
      title: 'Talk to a counsellor',
      desc: 'Changing subjects is a big step. A counsellor can help you weigh it with your school before deciding.',
      cta: 'Plan a review',
      to: '/plan',
    }
  }
  // Pre-selection learners (not_selected / unsure): the quiz is a recommended
  // reflection step, not a placement decision.
  if (!flags.quizDone) {
    return {
      title: 'Take the interest quiz',
      desc: 'Answer 30 quick questions about what you enjoy. Your results are guidance to help you reflect — not a placement decision.',
      cta: 'Start the quiz',
      to: '/assessment',
    }
  }
  return {
    title: 'Explore your results',
    desc: 'Your career personality is ready. Explore pathways connected to your interests and see what they involve.',
    cta: 'See my results',
    to: '/assessment/results',
  }
}

type Props = Flags

export default function NextStepCard(props: Props) {
  const step = getNextStep(props)

  return (
    <div className="next-step">
      <div className="next-step__eyebrow">Your next step</div>
      <div className="next-step__title">{step.title}</div>
      <p className="next-step__desc">{step.desc}</p>
      <Link to={step.to} className="next-step__cta">
        {step.cta}
        {ARROW}
      </Link>
    </div>
  )
}
