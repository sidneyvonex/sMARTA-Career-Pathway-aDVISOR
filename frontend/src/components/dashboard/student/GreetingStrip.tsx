import type { StudentProfile } from '../../../api/students'
import type { AssessmentResult } from '../../../api/assessment'

interface Props {
  profile: StudentProfile
  latestResult: AssessmentResult | null
  subjectCount: number
}

function greeting(name: string) {
  const h = new Date().getHours()
  if (h < 12) return `Good morning, ${name}`
  if (h < 17) return `Good afternoon, ${name}`
  return `Good evening, ${name}`
}

function initials(p: StudentProfile) {
  return `${p.first_name[0] ?? ''}${p.last_name[0] ?? ''}`.toUpperCase()
}

export default function GreetingStrip({ profile, latestResult, subjectCount }: Props) {
  const topPathway = latestResult?.recommendations[0]
  const fitPct = topPathway?.fit_pct ?? null

  return (
    <div className="greeting-strip" role="region" aria-label="Welcome banner">
      <div className="greeting-strip__avatar" aria-hidden="true">
        {initials(profile)}
      </div>

      <div className="greeting-strip__body">
        <div className="greeting-strip__hello">{greeting(profile.first_name)}</div>
        <div className="greeting-strip__name">{profile.first_name} {profile.last_name}</div>
        <div className="greeting-strip__chips">
          <span className="greeting-chip">Grade {profile.grade}</span>
          {profile.county && (
            <span className="greeting-chip" style={{ textTransform: 'capitalize' }}>
              {profile.county}
            </span>
          )}
          {topPathway && (
            <span className="greeting-chip greeting-chip--gold">
              {topPathway.pathway.name} · {fitPct}% fit
            </span>
          )}
        </div>
      </div>

      <div className="greeting-strip__tiles">
        <div className="greeting-tile">
          <div className="greeting-tile__value">{fitPct !== null ? `${fitPct}%` : '—'}</div>
          <div className="greeting-tile__label">Career match</div>
        </div>
        <div className="greeting-tile">
          <div className="greeting-tile__value">{subjectCount}</div>
          <div className="greeting-tile__label">Subjects</div>
        </div>
        <div className="greeting-tile">
          <div className="greeting-tile__value">{latestResult ? 'Done' : 'Pending'}</div>
          <div className="greeting-tile__label">Career quiz</div>
        </div>
      </div>
    </div>
  )
}
