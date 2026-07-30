import { useQueries, useQuery } from '@tanstack/react-query'
import { GRADE_LEVEL_POINTS, studentsApi } from '../../../api/students'
import { assessmentApi, type RIASECDimension } from '../../../api/assessment'
import { dashboardApi } from '../../../api/dashboard'
import { notificationsApi } from '../../../api/notifications'
import { useAuthStore } from '../../../store/authStore'
import { useNotificationStore } from '../../../store/notificationStore'
import { formatRelativeTime } from '../../../lib/format'
import { useDownloadReport } from '../../../hooks/useDownloadReport'
import LivelyStudentDashboard, { type LivelyData } from './lively/LivelyStudentDashboard'

const TRAIT_NAMES: Record<RIASECDimension, string> = {
  R: 'Hands-on',
  I: 'Curious',
  A: 'Creative',
  S: 'Social',
  E: 'Ambitious',
  C: 'Organised',
}

export default function StudentDashboard() {
  const { user } = useAuthStore()
  const { setDrawerOpen } = useNotificationStore()
  const { downloadReport, downloadingId } = useDownloadReport()

  const profileQ = useQuery({
    queryKey: ['student-profile'],
    queryFn: () => studentsApi.getProfile().then((response) => response.data.data),
  })

  const subjectsQ = useQuery({
    queryKey: ['my-subjects'],
    queryFn: () => studentsApi.getMySubjects().then((response) => response.data.data),
  })

  const resultQ = useQuery({
    queryKey: ['riasec-latest'],
    queryFn: () => assessmentApi.getLatest().then((response) => response.data.data),
    retry: false,
  })

  const counselorQ = useQuery({
    queryKey: ['student-counselor'],
    queryFn: () => dashboardApi.getStudentCounselor().then((response) => response.data.data),
  })

  const notificationsQ = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.getList().then((response) => response.data.data),
  })

  const subjects = subjectsQ.data ?? []
  const gradeQueries = useQueries({
    queries: subjects.map((subject) => ({
      queryKey: ['student-grades', subject.id],
      queryFn: () => studentsApi.getGrades(subject.id).then((response) => response.data.data),
      staleTime: 60_000,
    })),
  })

  const profile = profileQ.data ?? null
  const result = resultQ.data ?? null
  const counselor = counselorQ.data ?? null
  const notifications = notificationsQ.data ?? []

  if (profileQ.isLoading) {
    return (
      <div className="lv-loading" aria-label="Loading dashboard">
        <div className="skeleton lv-loading__hero" />
        <div className="skeleton lv-loading__side" />
        <div className="skeleton lv-loading__chart" />
        <div className="skeleton lv-loading__chart" />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="lv-load-error" role="alert">
        <span aria-hidden="true">↻</span>
        <h1>We could not load your dashboard.</h1>
        <p>Check your connection and try again.</p>
        <button type="button" className="btn-primary" onClick={() => window.location.reload()}>
          Try again
        </button>
      </div>
    )
  }

  const profileComplete = Boolean(profile.bio && profile.grade)
  const quizDone = result !== null
  const topPathway = result?.recommendations[0] ?? null
  const dimensions = result ? (Object.keys(result.scores) as RIASECDimension[]) : []
  const topDimension = dimensions.length
    ? dimensions.reduce((best, dimension) => (
        result!.scores[dimension] > result!.scores[best] ? dimension : best
      ))
    : null

  const gradeBuckets = new Map<string, { year: number; term: number; scores: number[] }>()
  gradeQueries.forEach((query) => {
    ;(query.data ?? []).forEach((grade) => {
      const key = `${grade.year}-${grade.term}`
      const bucket = gradeBuckets.get(key) ?? { year: grade.year, term: grade.term, scores: [] }
      bucket.scores.push(GRADE_LEVEL_POINTS[grade.level])
      gradeBuckets.set(key, bucket)
    })
  })

  const gradeTrend = Array.from(gradeBuckets.values())
    .sort((a, b) => a.year - b.year || a.term - b.term)
    .map((bucket) => ({
      term: `T${bucket.term} '${String(bucket.year).slice(-2)}`,
      points: Number(
        (bucket.scores.reduce((total, score) => total + score, 0) / bucket.scores.length).toFixed(1),
      ),
    }))

  const fullName = `${profile.first_name} ${profile.last_name}`.trim()
  const counselorName = counselor
    ? `${counselor.first_name} ${counselor.last_name}`.trim()
    : null

  const dashboardData: LivelyData = {
    firstName: profile.first_name,
    lastName: profile.last_name,
    photoUrl: profile.photo_url,
    gradeLabel: `Grade ${profile.grade}`,
    county: profile.county,
    profileComplete,
    quizDone,
    subjectsCount: subjects.length,
    topPathway: topPathway
      ? { name: topPathway.pathway.name, pct: topPathway.fit_pct }
      : null,
    topStrength: topDimension ? TRAIT_NAMES[topDimension] : null,
    radar: result
      ? dimensions.map((dimension) => ({
          label: TRAIT_NAMES[dimension],
          value: Math.round((result.scores[dimension] / 25) * 100),
        }))
      : null,
    pathwaySlices: result
      ? result.recommendations.slice(0, 3).map((recommendation) => ({
          name: recommendation.pathway.name,
          value: recommendation.fit_pct,
        }))
      : null,
    gradeTrend: gradeTrend.length ? gradeTrend : null,
    counselor: counselor && counselorName
      ? {
          name: counselorName,
          role: 'Guidance & Career Counselor',
          message: counselor.last_message ?? undefined,
          photoUrl: counselor.photo_url,
        }
      : null,
    activity: notifications.map((notification) => ({
      text: notification.message,
      time: formatRelativeTime(notification.created_at),
      actor: notification.type === 'counselor_note' && counselorName ? counselorName : fullName,
    })),
    onOpenActivity: () => setDrawerOpen(true),
    onDownloadReport: (quizDone || subjects.length > 0) && user
      ? () => downloadReport(user.id)
      : undefined,
    reportDownloading: downloadingId !== null,
  }

  return <LivelyStudentDashboard {...dashboardData} />
}
