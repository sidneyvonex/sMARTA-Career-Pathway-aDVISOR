import { useQuery } from '@tanstack/react-query'
import { studentsApi } from '../../../api/students'
import type { RIASECDimension } from '../../../api/assessment'
import { useAuthStore } from '../../../store/authStore'
import { useNotificationStore } from '../../../store/notificationStore'
import { formatRelativeTime } from '../../../lib/format'
import { useDownloadReport } from '../../../hooks/useDownloadReport'
import ErrorState from '../../common/dashboard/ErrorState'
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

  const dashboardQ = useQuery({
    queryKey: ['student', 'dashboard'],
    queryFn: () => studentsApi.getDashboard().then((response) => response.data.data),
  })

  const profile = dashboardQ.data?.profile ?? null
  const gradeSummary = dashboardQ.data?.grade_summary ?? null
  const result = dashboardQ.data?.assessment ?? null
  const counselor = dashboardQ.data?.counselor ?? null
  const notifications = dashboardQ.data?.notifications ?? []
  const evidence = dashboardQ.data?.evidence ?? null
  const choices = dashboardQ.data?.choices ?? []

  if (dashboardQ.isLoading) {
    return (
      <div className="lv-loading" aria-label="Loading dashboard">
        <div className="skeleton lv-loading__hero" />
        <div className="skeleton lv-loading__side" />
        <div className="skeleton lv-loading__chart" />
        <div className="skeleton lv-loading__chart" />
      </div>
    )
  }

  if (
    dashboardQ.isError ||
    !profile ||
    !evidence ||
    !gradeSummary
  ) {
    return (
      <ErrorState
        title="Your dashboard could not load"
        description="Check your connection and try loading your learner evidence and choices again."
        onRetry={() => dashboardQ.refetch()}
      />
    )
  }

  const quizDone = result !== null
  const topPathway = result?.recommendations[0] ?? null
  const dimensions = result ? (Object.keys(result.scores) as RIASECDimension[]) : []
  const topDimension = dimensions.length
    ? dimensions.reduce((best, dimension) => (
        result!.scores[dimension] > result!.scores[best] ? dimension : best
      ))
    : null

  const gradeTrend = gradeSummary.subjects.flatMap((subject) => {
    const records = [...subject.grades]
      .sort((a, b) => a.year - b.year || a.term - b.term || a.id - b.id)
      .map((grade) => ({
        period: `${grade.year} Term ${grade.term}`,
        level: grade.level,
      }))
    return records.length > 0
      ? [{ subject: subject.subject.name, records }]
      : []
  })

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
    quizDone,
    subjectsCount: gradeSummary.total_subjects,
    academicReady: evidence.academic_evidence.status === 'ready',
    savedChoicesCount: evidence.saved_combination_count,
    hasProvisionalChoice: choices.some((choice) => choice.status === 'provisional'),
    planStatus: evidence.plan_status,
    nextAction: evidence.next_action,
    topPathway: topPathway
      ? { name: topPathway.pathway.name }
      : null,
    topStrength: topDimension ? TRAIT_NAMES[topDimension] : null,
    radar: result
      ? dimensions.map((dimension) => ({
          label: TRAIT_NAMES[dimension],
          value: Math.round((result.scores[dimension] / 25) * 100),
        }))
      : null,
    pathways: result
      ? result.recommendations.slice(0, 3).map((recommendation) => ({
          name: recommendation.pathway.name,
          rank: recommendation.rank,
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
    interventions: dashboardQ.data?.interventions ?? [],
    onOpenActivity: () => setDrawerOpen(true),
    onDownloadReport: (quizDone || gradeSummary.total_subjects > 0) && user
      ? () => downloadReport(user.id)
      : undefined,
    reportDownloading: downloadingId !== null,
  }

  return <LivelyStudentDashboard {...dashboardData} />
}
