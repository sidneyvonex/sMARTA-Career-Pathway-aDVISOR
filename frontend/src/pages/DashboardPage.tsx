import { useAuthStore } from '../store/authStore'
import StudentDashboard from '../components/dashboard/student/StudentDashboard'
import CounselorDashboard from '../components/dashboard/counselor/CounselorDashboard'
import ParentDashboard from '../components/dashboard/parent/ParentDashboard'
import SchoolAdminDashboard from '../components/dashboard/admin/SchoolAdminDashboard'
import SystemAdminDashboard from '../components/system-admin/SystemAdminDashboard'

export default function DashboardPage() {
  const { user } = useAuthStore()

  if (!user) return null

  if (user.role === 'student') return <StudentDashboard />
  if (user.role === 'counselor') return <CounselorDashboard />
  if (user.role === 'parent') return <ParentDashboard />
  if (user.role === 'school_admin') return <SchoolAdminDashboard />
  if (user.role === 'system_admin') return <SystemAdminDashboard />

  return (
    <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
      Dashboard not yet available for your role.
    </div>
  )
}
