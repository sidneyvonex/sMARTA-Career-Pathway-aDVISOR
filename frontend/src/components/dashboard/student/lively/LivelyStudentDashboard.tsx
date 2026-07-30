import { lazy, Suspense } from 'react'
import { Link } from 'react-router-dom'
import DashboardHero from './DashboardHero'
import Avatar from '../../../common/Avatar'
import SectionHeader from '../../../common/dashboard/SectionHeader'
import type { RadarDatum } from './PersonalityRadar'
import type { GradePoint } from './GradeTrend'
import '../../../../styles/dashboard-lively.css'

const PersonalityRadar = lazy(() => import('./PersonalityRadar'))
const GradeTrend = lazy(() => import('./GradeTrend'))

const ChartSkeleton = () => <div className="lv-chart-skeleton" aria-hidden="true" />

export interface LivelyData {
  firstName: string
  lastName?: string
  photoUrl?: string | null
  gradeLabel?: string
  county?: string | null
  profileComplete: boolean
  quizDone: boolean
  subjectsCount: number
  topPathway: { name: string } | null
  topStrength: string | null
  radar: RadarDatum[] | null
  pathways: { name: string; rank: number }[] | null
  gradeTrend: GradePoint[] | null
  counselor: { name: string; role: string; message?: string; photoUrl?: string | null } | null
  activity: { text: string; time: string; actor?: string }[]
  onOpenActivity?: () => void
  onDownloadReport?: () => void
  reportDownloading?: boolean
}

const TASK_ICONS = {
  profile: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4" /><path d="M5 21c0-4 3-7 7-7s7 3 7 7" /></svg>,
  subjects: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 5a3 3 0 0 1 3-3h13v17H7a3 3 0 0 0-3 3V5z" /><path d="M4 19h16" /></svg>,
  quiz: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path d="M12 17v.01M9.8 9a2.4 2.4 0 1 1 3.4 2.2c-.8.4-1.2.9-1.2 1.8" /></svg>,
  explore: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path d="m15 9-2 4-4 2 2-4 4-2z" /></svg>,
}

function JourneyPanel({ data }: { data: LivelyData }) {
  const tasks = [
    data.profileComplete
      ? { to: '/profile', label: 'Refresh your profile', detail: 'Keep your interests and goals current', icon: TASK_ICONS.profile }
      : { to: '/profile', label: 'Complete your profile', detail: 'Help us personalise your guidance', icon: TASK_ICONS.profile },
    data.subjectsCount > 0
      ? { to: '/grades', label: 'Update your grades', detail: `${data.subjectsCount} subjects are ready to track`, icon: TASK_ICONS.subjects }
      : { to: '/grades', label: 'Add your subjects', detail: 'Start tracking your CBC progress', icon: TASK_ICONS.subjects },
    data.quizDone
      ? { to: '/assessment/results', label: 'Explore career ideas', detail: data.topPathway ? `Start with ${data.topPathway.name}` : 'See your interest-aligned pathways', icon: TASK_ICONS.explore }
      : { to: '/assessment', label: 'Take the career quiz', detail: 'Discover your natural strengths', icon: TASK_ICONS.quiz },
  ]

  return (
    <aside className="lv-journey lv-anim" style={{ ['--i' as string]: 1 }} aria-labelledby="journey-title">
      <SectionHeader
        className="lv-section-head"
        eyebrow="Keep moving"
        title="This week"
        titleId="journey-title"
        aside={<span className="lv-journey__count">{tasks.length} steps</span>}
      />
      <div className="lv-journey__tasks">
        {tasks.map((task, index) => (
          <Link to={task.to} className="lv-task" key={task.label}>
            <span className={`lv-task__icon lv-task__icon--${index}`}>{task.icon}</span>
            <span className="lv-task__copy">
              <strong>{task.label}</strong>
              <small>{task.detail}</small>
            </span>
            <svg className="lv-task__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="m9 18 6-6-6-6" />
            </svg>
          </Link>
        ))}
      </div>
      {data.onDownloadReport && (data.quizDone || data.subjectsCount > 0) && (
        <button
          type="button"
          className="lv-journey__report"
          onClick={data.onDownloadReport}
          disabled={data.reportDownloading}
        >
          {data.reportDownloading ? 'Preparing report…' : 'Download my progress report'}
        </button>
      )}
    </aside>
  )
}

function EmptyChart({ kind }: { kind: 'quiz' | 'grades' }) {
  const isQuiz = kind === 'quiz'
  return (
    <div className="lv-empty-chart">
      <span className="lv-empty-chart__mark" aria-hidden="true">{isQuiz ? '✦' : '↗'}</span>
      <strong>{isQuiz ? 'Your shape starts here' : 'Your trend starts here'}</strong>
      <p>{isQuiz ? 'Complete the quiz to reveal this chart.' : 'Add grades to see your progress over time.'}</p>
      <Link to={isQuiz ? '/assessment' : '/grades'}>{isQuiz ? 'Take the quiz' : 'Add grades'}</Link>
    </div>
  )
}

export default function LivelyStudentDashboard(data: LivelyData) {
  return (
    <div className="lv-dash">
      <div className="lv-overview">
        <div className="lv-anim" style={{ ['--i' as string]: 0 }}>
          <DashboardHero
            firstName={data.firstName}
            lastName={data.lastName}
            photoUrl={data.photoUrl}
            gradeLabel={data.gradeLabel}
            county={data.county}
            quizDone={data.quizDone}
            subjectsCount={data.subjectsCount}
            topPathway={data.topPathway}
          />
        </div>
        <JourneyPanel data={data} />
      </div>

      <section className="lv-insights" aria-labelledby="insights-title">
        <SectionHeader
          className="lv-section-head lv-section-head--wide"
          eyebrow="Your story in data"
          title="Career insights"
          titleId="insights-title"
          aside={data.topStrength
            ? <p>Your strongest signal is <strong>{data.topStrength}</strong>.</p>
            : undefined}
        />

        <div className="lv-chart-grid">
          <article className="lv-card lv-card--radar lv-anim" style={{ ['--i' as string]: 2 }}>
            <SectionHeader
              className="lv-card__head"
              eyebrow="Personality"
              title="Your strength shape"
              titleAs="h3"
              action={data.quizDone ? { label: 'Full results', to: '/assessment/results' } : undefined}
            />
            {data.radar
              ? <Suspense fallback={<ChartSkeleton />}><PersonalityRadar data={data.radar} /></Suspense>
              : <EmptyChart kind="quiz" />}
          </article>

          <article className="lv-card lv-card--pathway lv-anim" style={{ ['--i' as string]: 3 }}>
            <SectionHeader className="lv-card__head" eyebrow="Direction" title="Interest-aligned pathways" titleAs="h3" />
            {data.pathways && data.topPathway ? (
              <div>
                <p className="lv-pathway-advisory">
                  These suggestions are starting points for exploration, not predictions or placements.
                </p>
                <div className="lv-legend">
                  {data.pathways.map((pathway, index) => (
                    <span key={pathway.name} className="lv-legend__item">
                      <i className={`lv-legend__dot lv-legend__dot--${index}`} />
                      <span>{pathway.name}</span>
                      <strong>{pathway.rank === 1 ? 'Strongest alignment' : `Explore #${pathway.rank}`}</strong>
                    </span>
                  ))}
                </div>
              </div>
            ) : <EmptyChart kind="quiz" />}
          </article>

          <article className="lv-card lv-card--trend lv-anim" style={{ ['--i' as string]: 4 }}>
            <SectionHeader
              className="lv-card__head"
              eyebrow="Progress"
              title="Your grade trend"
              titleAs="h3"
              action={data.subjectsCount > 0 ? { label: 'My grades', to: '/grades' } : undefined}
            />
            {data.gradeTrend && data.gradeTrend.length > 0
              ? <Suspense fallback={<ChartSkeleton />}><GradeTrend data={data.gradeTrend} /></Suspense>
              : <EmptyChart kind="grades" />}
            <div className="lv-trend-summary">
              <strong>{data.subjectsCount}</strong>
              <span>subject{data.subjectsCount === 1 ? '' : 's'} enrolled</span>
            </div>
          </article>
        </div>
      </section>

      <section className="lv-people-grid" aria-label="Support and recent activity">
        <article className="lv-card lv-card--counselor lv-anim" style={{ ['--i' as string]: 5 }}>
          <span className="lv-card__sun" aria-hidden="true" />
          <SectionHeader className="lv-card__head" eyebrow="Your support" title="Career counsellor" titleAs="h3" />
          {data.counselor ? (
            <>
              <div className="lv-counselor">
                <Avatar seed={data.counselor.name} photoUrl={data.counselor.photoUrl} size={62} shape="squircle" />
                <div>
                  <div className="lv-counselor__name">{data.counselor.name}</div>
                  <div className="lv-counselor__role">{data.counselor.role}</div>
                </div>
              </div>
              {data.counselor.message && <blockquote className="lv-counselor__msg">“{data.counselor.message}”</blockquote>}
            </>
          ) : (
            <div className="lv-counselor__empty">
              <span aria-hidden="true">◎</span>
              <p>A counselor will appear here when your school assigns one.</p>
            </div>
          )}
        </article>

        <article className="lv-card lv-card--activity lv-anim" style={{ ['--i' as string]: 6 }}>
          <SectionHeader
            className="lv-card__head"
            eyebrow="Latest"
            title="Recent activity"
            titleAs="h3"
            action={data.activity.length > 0 && data.onOpenActivity
              ? { label: 'See all', onClick: data.onOpenActivity }
              : undefined}
          />
          {data.activity.length > 0 ? data.activity.slice(0, 4).map((item, index) => (
            <div key={`${item.text}-${index}`} className="lv-act">
              <Avatar seed={item.actor ?? data.firstName} size={40} shape="squircle" />
              <div className="lv-act__copy">
                <div className="lv-act__text">{item.text}</div>
                <div className="lv-act__time">{item.time}</div>
              </div>
            </div>
          )) : (
            <div className="lv-activity-empty">
              <strong>Your journey is ready.</strong>
              <span>New milestones and counselor notes will appear here.</span>
            </div>
          )}
        </article>
      </section>

      <aside className="lv-quote lv-anim" style={{ ['--i' as string]: 7 }}>
        <div className="lv-quote__students" aria-hidden="true">
          <Avatar seed="Njeri" size={54} shape="squircle" />
          <Avatar seed="Baraka" size={54} shape="squircle" />
          <Avatar seed="Akinyi" size={54} shape="squircle" />
        </div>
        <p><span>“</span>Elimu ni ufunguo wa maisha. <strong>Tayarisha kesho yako leo.</strong></p>
        <div className="lv-quote__landscape" aria-hidden="true" />
      </aside>
    </div>
  )
}
