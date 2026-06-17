import { Link } from 'react-router-dom'

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

function getNextStep(flags: {
  profileComplete: boolean
  hasSubjects: boolean
  quizDone: boolean
  counselorAssigned: boolean
}): Step {
  if (!flags.profileComplete) {
    return {
      title: 'Complete your profile',
      desc: 'Tell us about yourself — your grade, interests, and county — so we can match you with the right career paths.',
      cta: 'Complete profile',
      to: '/profile',
    }
  }
  if (!flags.hasSubjects) {
    return {
      title: 'Add your subjects',
      desc: 'Select the subjects you\'re taking this year. We\'ll use them alongside your quiz results to refine your career matches.',
      cta: 'Choose subjects',
      to: '/grades',
    }
  }
  if (!flags.quizDone) {
    return {
      title: 'Take the career quiz',
      desc: 'Answer 30 quick questions about what you enjoy. We\'ll map your personality to careers that fit you best.',
      cta: 'Start the quiz',
      to: '/assessment',
    }
  }
  return {
    title: 'Explore your results',
    desc: 'Your career personality is ready. See which pathways match you best and what they look like in practice.',
    cta: 'See my results',
    to: '/assessment/results',
  }
}

interface Props {
  profileComplete: boolean
  hasSubjects: boolean
  quizDone: boolean
  counselorAssigned: boolean
}

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
