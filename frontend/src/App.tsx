import { lazy, Suspense } from 'react'
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
import LandingPage from './pages/LandingPage'
import AboutPage from './pages/AboutPage'
import PathwaysPage from './pages/PathwaysPage'
import HowItWorksPage from './pages/HowItWorksPage'
import ForSchoolsPage from './pages/ForSchoolsPage'
import { useAuth } from './hooks/useAuth'
import { useAuthStore } from './store/authStore'
import { useNotificationPoll } from './hooks/useNotificationPoll'
import { usePWAUpdate } from './hooks/usePWAUpdate'
import InstallBanner from './components/InstallBanner'
import ErrorBoundary from './components/common/ErrorBoundary'
import ErrorState from './components/common/dashboard/ErrorState'
import LoadingSkeleton from './components/common/dashboard/LoadingSkeleton'
import { isFeatureEnabled } from './lib/featureFlags'

const StudentProfilePage = lazy(() => import('./pages/StudentProfilePage'))
const GradesPage = lazy(() => import('./pages/GradesPage'))
const AssessmentPage = lazy(() => import('./pages/AssessmentPage'))
const AssessmentResultsPage = lazy(() => import('./pages/AssessmentResultsPage'))
const CombinationExplorerPage = lazy(() => import('./pages/CombinationExplorerPage'))
const CombinationComparePage = lazy(() => import('./pages/CombinationComparePage'))
const LearnerPlanPage = lazy(() => import('./pages/LearnerPlanPage'))
const ParentAccessPage = lazy(() => import('./pages/ParentAccessPage'))
const EducationGoalsPage = lazy(() => import('./pages/EducationGoalsPage'))
const StudentListPage = lazy(() => import('./pages/counselor/StudentListPage'))
const StudentDetailPage = lazy(() => import('./pages/counselor/StudentDetailPage'))
const NotesListPage = lazy(() => import('./pages/counselor/NotesListPage'))
const SchoolProfilePage = lazy(() => import('./pages/admin/SchoolProfilePage'))
const CounselorManagementPage = lazy(() => import('./pages/admin/CounselorManagementPage'))
const SchoolStudentsPage = lazy(() => import('./pages/admin/SchoolStudentsPage'))
const SchoolOfferingsPage = lazy(() => import('./pages/admin/SchoolOfferingsPage'))
const ChildDetailPage = lazy(() => import('./pages/parent/ChildDetailPage'))
const SystemAdminSchoolsPage = lazy(() => import('./pages/system-admin/SystemAdminSchoolsPage'))
const SystemAdminUsersPage = lazy(() => import('./pages/system-admin/SystemAdminUsersPage'))
const SystemAdminAuditLogPage = lazy(() => import('./pages/system-admin/SystemAdminAuditLogPage'))
const SystemAdminCataloguePage = lazy(() => import('./pages/system-admin/SystemAdminCataloguePage'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 1000 * 60 * 5 } },
})

function RootRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading…</div>
  }

  if (!isAuthenticated) {
    return <LandingPage />
  }

  return (
    <Shell>
      <DashboardPage />
    </Shell>
  )
}

function AppRoutes() {
  useAuth()
  useNotificationPoll()
  usePWAUpdate()

  return (
    <Routes>
      {/* Public auth pages — no Shell */}
      <Route path="/" element={<RootRoute />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/pathways" element={<PathwaysPage />} />
      <Route path="/how-it-works" element={<HowItWorksPage />} />
      <Route path="/for-schools" element={<ForSchoolsPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/accept-invite" element={<AcceptInvitePage />} />

      {/* Authenticated pages — wrapped in Shell */}
      <Route element={<ProtectedRoute />}>
        <Route element={(
          <Suspense fallback={<LoadingSkeleton label="Loading page" rows={4} />}>
            <Shell />
          </Suspense>
        )}>
          <Route element={<ProtectedRoute roles={['student']} />}>
            <Route path="/profile" element={<StudentProfilePage />} />
            <Route path="/grades" element={<GradesPage />} />
            {isFeatureEnabled('academic_progress_v1') && (
              <Route path="/education-goals" element={<EducationGoalsPage />} />
            )}
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/assessment/results" element={<AssessmentResultsPage />} />
            <Route path="/explore" element={<CombinationExplorerPage />} />
            <Route path="/compare" element={<CombinationComparePage />} />
            <Route path="/plan" element={<LearnerPlanPage />} />
            <Route path="/access" element={<ParentAccessPage />} />
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
            <Route path="/admin/offerings" element={<SchoolOfferingsPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['parent']} />}>
            <Route path="/parent/child/:id" element={<ChildDetailPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['system_admin']} />}>
            <Route path="/system-admin/catalogue" element={<SystemAdminCataloguePage />} />
            <Route path="/system-admin/schools" element={<SystemAdminSchoolsPage />} />
            <Route path="/system-admin/users" element={<SystemAdminUsersPage />} />
            <Route path="/system-admin/audit-log" element={<SystemAdminAuditLogPage />} />
          </Route>

          <Route path="*" element={(
            <ErrorState
              title="Page not found"
              description="This page does not exist or is not available for your account."
              secondaryAction={{ label: 'Return to dashboard', to: '/' }}
            />
          )} />
        </Route>
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary scope="application">
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
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
