import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import ProtectedRoute from './components/ProtectedRoute'
import Shell from './components/shell/Shell'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import AcceptInvitePage from './pages/AcceptInvitePage'
import DashboardPage from './pages/DashboardPage'
import StudentProfilePage from './pages/StudentProfilePage'
import GradesPage from './pages/GradesPage'
import AssessmentPage from './pages/AssessmentPage'
import AssessmentResultsPage from './pages/AssessmentResultsPage'
import StudentListPage from './pages/counselor/StudentListPage'
import StudentDetailPage from './pages/counselor/StudentDetailPage'
import NotesListPage from './pages/counselor/NotesListPage'
import SchoolProfilePage from './pages/admin/SchoolProfilePage'
import CounselorManagementPage from './pages/admin/CounselorManagementPage'
import SchoolStudentsPage from './pages/admin/SchoolStudentsPage'
import ChildDetailPage from './pages/parent/ChildDetailPage'
import SystemAdminSchoolsPage from './pages/system-admin/SystemAdminSchoolsPage'
import SystemAdminUsersPage from './pages/system-admin/SystemAdminUsersPage'
import SystemAdminAuditLogPage from './pages/system-admin/SystemAdminAuditLogPage'
import { useAuth } from './hooks/useAuth'
import { useNotificationPoll } from './hooks/useNotificationPoll'
import { usePWAUpdate } from './hooks/usePWAUpdate'
import InstallBanner from './components/InstallBanner'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 1000 * 60 * 5 } },
})

function AppRoutes() {
  useAuth()
  useNotificationPoll()
  usePWAUpdate()

  return (
    <Routes>
      {/* Public auth pages — no Shell */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/accept-invite" element={<AcceptInvitePage />} />

      {/* Authenticated pages — wrapped in Shell */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Shell />}>
          <Route path="/" element={<DashboardPage />} />

          <Route element={<ProtectedRoute roles={['student']} />}>
            <Route path="/profile" element={<StudentProfilePage />} />
            <Route path="/grades" element={<GradesPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/assessment/results" element={<AssessmentResultsPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['counselor']} />}>
            <Route path="/counselor/students" element={<StudentListPage />} />
            <Route path="/counselor/students/:id" element={<StudentDetailPage />} />
            <Route path="/counselor/notes" element={<NotesListPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['school_admin']} />}>
            <Route path="/admin/school" element={<SchoolProfilePage />} />
            <Route path="/admin/counselors" element={<CounselorManagementPage />} />
            <Route path="/admin/students" element={<SchoolStudentsPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['parent']} />}>
            <Route path="/parent/child/:id" element={<ChildDetailPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['system_admin']} />}>
            <Route path="/system-admin/schools" element={<SystemAdminSchoolsPage />} />
            <Route path="/system-admin/users" element={<SystemAdminUsersPage />} />
            <Route path="/system-admin/audit-log" element={<SystemAdminAuditLogPage />} />
          </Route>

          <Route path="*" element={
            <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
              <h2 style={{ color: 'var(--color-text)', marginBottom: 'var(--space-2)' }}>Page not found</h2>
              <p>This page doesn't exist or is coming soon.</p>
            </div>
          } />
        </Route>
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <InstallBanner />
        <Toaster
          position="top-right"
          toastOptions={{
            style: { fontFamily: 'Inter, system-ui, sans-serif', fontSize: '0.875rem' },
            success: { iconTheme: { primary: '#1A5C38', secondary: '#fff' } },
            error: { iconTheme: { primary: '#B91C1C', secondary: '#fff' } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
