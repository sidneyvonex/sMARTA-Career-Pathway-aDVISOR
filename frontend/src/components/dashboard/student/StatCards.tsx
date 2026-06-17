import type { CounselorInfo } from '../../../api/dashboard'

interface Props {
  fitPct: number | null
  subjectCount: number
  quizDone: boolean
  counselor: CounselorInfo | null
}

function Sparkline({ color = 'var(--color-primary)' }: { color?: string }) {
  return (
    <svg width="60" height="24" viewBox="0 0 60 24" aria-hidden="true" className="sparkline">
      <polyline
        points="0,20 10,17 20,14 30,16 40,10 50,7 60,4"
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function StatCards({ fitPct, subjectCount, quizDone, counselor }: Props) {
  return (
    <div className="stat-cards">
      <div className="stat-card">
        <div className="stat-card__label">Career match</div>
        <div className="stat-card__value">{fitPct !== null ? `${fitPct}%` : '—'}</div>
        <div className="stat-card__sub">Based on your quiz results</div>
        <Sparkline color="var(--color-primary)" />
      </div>

      <div className="stat-card">
        <div className="stat-card__label">Subjects enrolled</div>
        <div className="stat-card__value">{subjectCount}</div>
        <div className="stat-card__sub">Added to your list</div>
        <Sparkline color="var(--color-primary-light)" />
      </div>

      <div className="stat-card">
        <div className="stat-card__label">Career quiz</div>
        <div className="stat-card__value" style={{ color: quizDone ? 'var(--color-success)' : 'var(--color-text-secondary)' }}>
          {quizDone ? 'Complete' : 'Not done'}
        </div>
        <div className="stat-card__sub">
          {quizDone ? 'Results available' : 'Start when ready'}
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-card__label">Counselor</div>
        <div className="stat-card__value" style={{ fontSize: 'var(--font-size-base)', fontWeight: 600 }}>
          {counselor ? `${counselor.first_name} ${counselor.last_name}` : 'Not assigned'}
        </div>
        <div className="stat-card__sub">
          {counselor?.last_message ? 'New message' : counselor ? 'No new messages' : 'Assigned in school mode'}
        </div>
      </div>
    </div>
  )
}
