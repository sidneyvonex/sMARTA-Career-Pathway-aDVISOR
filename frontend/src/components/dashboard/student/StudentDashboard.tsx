import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studentsApi } from '../../../api/students'
import { assessmentApi } from '../../../api/assessment'
import { dashboardApi } from '../../../api/dashboard'
import { notificationsApi } from '../../../api/notifications'
import GreetingStrip from './GreetingStrip'
import JourneyStrip from './JourneyStrip'
import StatCards from './StatCards'
import TraitBars from './TraitBars'
import CareerPathways from './CareerPathways'
import CounselorCard from './CounselorCard'
import ActivityFeed from './ActivityFeed'
import '../../../styles/dashboard.css'

function SkeletonCard({ height = 160 }: { height?: number }) {
  return (
    <div className="skeleton-card">
      <div className="skeleton" style={{ height: 16, width: '40%' }} />
      <div className="skeleton" style={{ height: height - 60 }} />
    </div>
  )
}

export default function StudentDashboard() {
  const profileQ = useQuery({
    queryKey: ['student-profile'],
    queryFn: () => studentsApi.getProfile().then((r) => r.data.data),
  })

  const subjectsQ = useQuery({
    queryKey: ['my-subjects'],
    queryFn: () => studentsApi.getMySubjects().then((r) => r.data.data),
  })

  const resultQ = useQuery({
    queryKey: ['riasec-latest'],
    queryFn: () => assessmentApi.getLatest().then((r) => r.data.data),
    retry: false,
  })

  const counselorQ = useQuery({
    queryKey: ['student-counselor'],
    queryFn: () => dashboardApi.getStudentCounselor().then((r) => r.data.data),
  })

  const notifQ = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.getList().then((r) => r.data.data),
  })

  const profile = profileQ.data ?? null
  const subjects = subjectsQ.data ?? []
  const result = resultQ.data ?? null
  const counselor = counselorQ.data ?? null
  const notifications = notifQ.data ?? []

  if (profileQ.isLoading) {
    return (
      <div>
        <div className="skeleton" style={{ height: 140, borderRadius: 13, marginBottom: 'var(--space-5)' }} />
        <div className="stat-cards">
          {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} height={100} />)}
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        Couldn't load your profile. <button className="activity-feed__see-all" onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  const fitPct = result?.recommendations[0]?.fit_pct ?? null
  const profileComplete = !!(profile.bio && profile.grade)

  return (
    <div>
      <GreetingStrip
        profile={profile}
        latestResult={result}
        subjectCount={subjects.length}
      />

      <JourneyStrip
        profileComplete={profileComplete}
        subjectCount={subjects.length}
        quizDone={result !== null}
        counselorAssigned={counselor !== null}
      />

      <div className="quick-actions">
        <Link to="/assessment/results" className="btn-primary">
          See my career results
        </Link>
        <Link to="/grades" className="btn-ghost">
          Update grades
        </Link>
        <Link to="/profile" className="btn-accent">
          Edit profile
        </Link>
      </div>

      <StatCards
        fitPct={fitPct}
        subjectCount={subjects.length}
        quizDone={result !== null}
        counselor={counselor}
      />

      <div className="dashboard-grid">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
          {result ? (
            <TraitBars result={result} />
          ) : (
            <div className="dashboard-card">
              <p className="dashboard-card__title">How you see the world</p>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                Take the career quiz to see your personality traits.
              </p>
            </div>
          )}

          <div className="dashboard-card">
            <p className="dashboard-card__title">Your grades</p>
            {subjects.length === 0 ? (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                No subjects added yet. <Link to="/grades">Add subjects</Link>
              </p>
            ) : (
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {subjects.slice(0, 6).map((ss) => (
                  <li key={ss.id} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--color-primary)', flexShrink: 0 }} aria-hidden="true" />
                    {ss.subject.name}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
          {result ? (
            <CareerPathways result={result} />
          ) : (
            <div className="dashboard-card">
              <p className="dashboard-card__title">Best careers for you</p>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                Complete the career quiz to see your top pathways.
              </p>
            </div>
          )}

          <CounselorCard counselor={counselor} />

          <ActivityFeed notifications={notifications} />
        </div>
      </div>
    </div>
  )
}
