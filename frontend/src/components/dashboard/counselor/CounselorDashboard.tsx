import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../../store/authStore'
import { dashboardApi } from '../../../api/dashboard'
import { greeting } from '../../../lib/greeting'
import AssessmentRing from './AssessmentRing'
import StudentList from './StudentList'
import Avatar from '../../common/Avatar'
import DashboardHero from '../../common/dashboard/DashboardHero'
import ErrorState from '../../common/dashboard/ErrorState'
import LoadingSkeleton from '../../common/dashboard/LoadingSkeleton'
import MetricCard from '../../common/dashboard/MetricCard'
import SectionHeader from '../../common/dashboard/SectionHeader'
import '../../../styles/dashboard.css'

export default function CounselorDashboard() {
  const { user } = useAuthStore()

  const studentsQ = useQuery({
    queryKey: ['counselor', 'students'],
    queryFn: () => dashboardApi.getCounselorStudents().then((r) => r.data.data),
  })

  const statsQ = useQuery({
    queryKey: ['counselor', 'stats'],
    queryFn: () => dashboardApi.getCounselorStats().then((r) => r.data.data),
  })

  const students = studentsQ.data ?? []
  const stats = statsQ.data ?? { total_students: 0, assessments_done: 0, students_needing_attention: 0, notes_written: 0 }

  if (studentsQ.isLoading || statsQ.isLoading) {
    return <LoadingSkeleton label="Loading counsellor dashboard" rows={4} variant="metrics" />
  }

  if (studentsQ.isError || statsQ.isError) {
    return (
      <ErrorState
        title="The counsellor dashboard could not load"
        description="Check your connection and try loading the learner caseload again."
        onRetry={() => {
          studentsQ.refetch()
          statsQ.refetch()
        }}
      />
    )
  }

  const fullName = user ? `${user.first_name} ${user.last_name}`.trim() : 'Counsellor'

  return (
    <div className="db-page">
      <DashboardHero
        tone="counsellor"
        eyebrow="Counsellor workspace"
        title={user ? greeting(user.first_name) : 'Welcome'}
        description={stats.students_needing_attention > 0
          ? `${stats.students_needing_attention} learner${stats.students_needing_attention === 1 ? '' : 's'} need a follow-up.`
          : 'Your assigned learners are up to date.'}
        avatar={<Avatar seed={fullName} size={46} shape="squircle" />}
        meta={[
          user?.county ? `${user.county} County` : '',
          `${stats.total_students} learner${stats.total_students === 1 ? '' : 's'} assigned`,
        ]}
        actions={[{ label: 'Add a learner note', to: '/counselor/notes' }]}
      />

      <div className="db-metric-grid">
        <MetricCard label="Total students" value={stats.total_students} detail="Assigned to you" to="/counselor/students" />
        <MetricCard
          label="Assessments done"
          value={stats.assessments_done}
          detail={stats.total_students > 0
            ? `${Math.round((stats.assessments_done / stats.total_students) * 100)}% complete`
            : 'No learners yet'}
          tone="positive"
        />
        <MetricCard
          label="Need attention"
          value={stats.students_needing_attention}
          detail="Assessment follow-up"
          tone={stats.students_needing_attention > 0 ? 'warning' : 'neutral'}
          to="/counselor/students"
        />
        <MetricCard label="Notes written" value={stats.notes_written} detail="Across all learners" to="/counselor/notes" />
      </div>

      <section className="db-content-grid" aria-label="Counsellor caseload and assessment progress">
        <StudentList students={students} />

        <aside className="db-panel db-panel--compact">
          <SectionHeader eyebrow="Coverage" title="Assessment progress" titleAs="h3" />
          <AssessmentRing done={stats.assessments_done} total={stats.total_students} />
        </aside>
      </section>
    </div>
  )
}
