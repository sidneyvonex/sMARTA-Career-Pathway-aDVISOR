import { useAuthStore } from '../store/authStore'
import StudentDashboard from '../components/dashboard/student/StudentDashboard'
import CounselorDashboard from '../components/dashboard/counselor/CounselorDashboard'
import ParentDashboard from '../components/dashboard/parent/ParentDashboard'

export default function DashboardPage() {
  const { user } = useAuthStore()

  if (!user) return null

  if (user.role === 'student') return <StudentDashboard />
  if (user.role === 'counselor') return <CounselorDashboard />
  if (user.role === 'parent') return <ParentDashboard />

  return (
    <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
      Dashboard not yet available for your role.
    </div>
  )
}
