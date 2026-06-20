import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studentsApi } from '../../../api/students'
import { assessmentApi } from '../../../api/assessment'
import { dashboardApi } from '../../../api/dashboard'
import { notificationsApi } from '../../../api/notifications'
import { useAuthStore } from '../../../store/authStore'
import { useNotificationStore } from '../../../store/notificationStore'
import { greeting } from '../../../lib/greeting'
import { initials, formatRelativeTime } from '../../../lib/format'
import type { RIASECDimension } from '../../../api/assessment'
import { useDownloadReport } from '../../../hooks/useDownloadReport'
import NextStepCard from './NextStepCard'
import JourneyProgress from './JourneyProgress'
import '../../../styles/dashboard.css'

const TRAIT_NAMES: Record<RIASECDimension, string> = {
  R: 'Hands-on', I: 'Curious', A: 'Creative',
  S: 'Social', E: 'Ambitious', C: 'Organised',
}

const MAX_SCORE = 25

const BELL_ICON = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
)

const LOCK_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0110 0v4" />
  </svg>
)

const CHART_ICON = (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M7 20V10m5 10V4m5 16v-7" />
  </svg>
)

export default function StudentDashboard() {
  const { user } = useAuthStore()
  const { setDrawerOpen } = useNotificationStore()
  const { downloadReport, isDownloading } = useDownloadReport()

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
      <div className="dashboard">
        <div className="skeleton" style={{ height: 52, borderRadius: 'var(--radius-md)' }} />
        <div className="skeleton" style={{ height: 180, borderRadius: 16 }} />
        <div className="skeleton" style={{ height: 40, borderRadius: 'var(--radius-md)' }} />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="dashboard" style={{ textAlign: 'center', padding: 'var(--space-12) 0', color: 'var(--color-text-secondary)' }}>
        <p>Could not load your profile.</p>
        <button type="button" className="dash-card__link" onClick={() => window.location.reload()} style={{ marginTop: 'var(--space-2)' }}>
          Try again
        </button>
      </div>
    )
  }

  const profileComplete = !!(profile.bio && profile.grade)
  const hasSubjects = subjects.length > 0
  const quizDone = result !== null
  const counselorAssigned = counselor !== null
  const topPathway = result?.recommendations[0]
  const canDownload = quizDone || hasSubjects

  return (
    <div className="dashboard">
      {/* Compact greeting */}
      <div className="dash-greeting">
        <div className="dash-greeting__avatar">
          {initials(profile.first_name, profile.last_name)}
        </div>
        <div className="dash-greeting__text">
          <div className="dash-greeting__name">{greeting(profile.first_name)}</div>
          <div className="dash-greeting__meta">
            <span className="dash-greeting__chip">Grade {profile.grade}</span>
            {profile.county && <span className="dash-greeting__chip" style={{ textTransform: 'capitalize' }}>{profile.county}</span>}
            {topPathway && (
              <span className="dash-greeting__chip" style={{ background: 'var(--color-accent-surface)', color: 'var(--color-accent)' }}>
                {topPathway.pathway.name} &middot; {topPathway.fit_pct}%
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Next step card */}
      {!(quizDone && profileComplete && hasSubjects) && (
        <NextStepCard
          profileComplete={profileComplete}
          hasSubjects={hasSubjects}
          quizDone={quizDone}
          counselorAssigned={counselorAssigned}
        />
      )}

      {/* Journey progress */}
      <JourneyProgress
        profileComplete={profileComplete}
        hasSubjects={hasSubjects}
        quizDone={quizDone}
        counselorAssigned={counselorAssigned}
      />

      {/* Quick stats — only show non-zero stats */}
      {(hasSubjects || quizDone) && (
        <div className="quick-stats">
          {hasSubjects && (
            <div className="quick-stat">
              <div className="quick-stat__value">{subjects.length}</div>
              <div className="quick-stat__label">Subjects enrolled</div>
              <Link to="/grades" className="quick-stat__action">Manage subjects</Link>
            </div>
          )}
          {topPathway && (
            <div className="quick-stat">
              <div className="quick-stat__value">{topPathway.fit_pct}%</div>
              <div className="quick-stat__label">Career match</div>
              <Link to="/assessment/results" className="quick-stat__action">View results</Link>
            </div>
          )}
          {counselorAssigned && (
            <div className="quick-stat">
              <div className="quick-stat__value" style={{ fontSize: 'var(--font-size-base)' }}>
                {counselor?.first_name} {counselor?.last_name}
              </div>
              <div className="quick-stat__label">Your counselor</div>
            </div>
          )}
        </div>
      )}

      {/* Career personality — shown after quiz, locked before */}
      {quizDone && result ? (
        <div className="dash-grid">
          <div className="dash-card">
            <div className="dash-card__header">
              <span className="dash-card__title">Your personality</span>
              <Link to="/assessment/results" className="dash-card__link">Full results</Link>
            </div>
            {(Object.keys(result.scores) as RIASECDimension[])
              .sort((a, b) => result.scores[b] - result.scores[a])
              .slice(0, 3)
              .map((dim, i) => {
                const pct = Math.round((result.scores[dim] / MAX_SCORE) * 100)
                const fillClass = i === 0 ? 'trait-bar__fill--top' : i === 1 ? 'trait-bar__fill--mid' : 'trait-bar__fill--low'
                return (
                  <div key={dim} className="trait-bar">
                    <div className="trait-bar__header">
                      <span className="trait-bar__name">{TRAIT_NAMES[dim]}</span>
                      <span className="trait-bar__pct">{pct}%</span>
                    </div>
                    <div className="trait-bar__track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
                      <div className={`trait-bar__fill ${fillClass}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
          </div>

          <div className="dash-card">
            <div className="dash-card__header">
              <span className="dash-card__title">Best career paths</span>
            </div>
            {result.recommendations.slice(0, 3).map((rec) => (
              <div key={rec.rank} className={`pathway-item${rec.rank === 1 ? ' pathway-item--first' : ''}`}>
                <span className="pathway-item__rank">{rec.rank}</span>
                <div className="pathway-item__info">
                  <div className="pathway-item__name">{rec.pathway.name}</div>
                </div>
                <span className="pathway-item__pct">{rec.fit_pct}%</span>
              </div>
            ))}
          </div>
        </div>
      ) : !quizDone ? (
        <div className="locked-section">
          <div className="locked-section__icon">{LOCK_ICON}</div>
          <div className="locked-section__body">
            <div className="locked-section__title">Career personality</div>
            <div className="locked-section__desc">
              Take the career quiz to discover your strengths and see which career paths match you best.
            </div>
          </div>
          <Link to="/assessment" className="locked-section__link">Take quiz</Link>
        </div>
      ) : null}

      {/* Grades preview — only if has subjects */}
      {hasSubjects && (
        <div className="locked-section">
          <div className="locked-section__icon">{CHART_ICON}</div>
          <div className="locked-section__body">
            <div className="locked-section__title">{subjects.length} subject{subjects.length !== 1 ? 's' : ''} enrolled</div>
            <div className="locked-section__desc">
              {subjects.slice(0, 3).map((s) => s.subject.name).join(', ')}
              {subjects.length > 3 ? ` and ${subjects.length - 3} more` : ''}
            </div>
          </div>
          <Link to="/grades" className="locked-section__link">View grades</Link>
        </div>
      )}

      {/* Counselor card */}
      {counselorAssigned && counselor && (
        <div className="counselor-card">
          <div className="counselor-card__header">
            <div className="counselor-card__avatar">{initials(counselor.first_name, counselor.last_name)}</div>
            <div>
              <div className="counselor-card__name">{counselor.first_name} {counselor.last_name}</div>
              <div className="counselor-card__role">Career Counselor</div>
            </div>
          </div>
          {counselor.last_message ? (
            <blockquote className="counselor-card__message">"{counselor.last_message}"</blockquote>
          ) : (
            <p className="counselor-card__empty">No messages yet.</p>
          )}
        </div>
      )}

      {/* Activity feed — only if there are notifications */}
      {notifications.length > 0 && (
        <div className="dash-card">
          <div className="dash-card__header">
            <span className="dash-card__title">Recent activity</span>
            <button type="button" className="dash-card__link" onClick={() => setDrawerOpen(true)}>See all</button>
          </div>
          {notifications.slice(0, 3).map((n) => (
            <div key={n.id} className="activity-item">
              <div className="activity-item__icon">{BELL_ICON}</div>
              <div>
                <span className="activity-item__text">{n.message}</span>
                <span className="activity-item__time">{formatRelativeTime(n.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Download report */}
      {canDownload && (
        <div className="dash-card" style={{ textAlign: 'center' }}>
          <button
            type="button"
            className="btn-primary"
            onClick={() => downloadReport(user!.id)}
            disabled={isDownloading}
            style={{ minHeight: 'var(--min-touch-target)' }}
          >
            {isDownloading ? 'Generating…' : 'Download Report'}
          </button>
        </div>
      )}
    </div>
  )
}
