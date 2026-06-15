import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import AcceptInvitePage from './pages/AcceptInvitePage'
import { useAuth } from './hooks/useAuth'
import StudentProfilePage from './pages/StudentProfilePage'
import GradesPage from './pages/GradesPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 1000 * 60 * 5 } },
})

function AppRoutes() {
  useAuth()

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/accept-invite" element={<AcceptInvitePage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={
          <main style={{ padding: '2rem', textAlign: 'center' }}>
            <img src="/logo.png" alt="Smarta Shauri" style={{ width: '80px', margin: '0 auto 1rem' }} />
            <h1 style={{ color: 'var(--color-primary)', fontWeight: 700 }}>Smarta Shauri</h1>
            <p style={{ color: 'var(--color-text-secondary)' }}>Discover. Plan. Choose. Succeed.</p>
          </main>
        } />
      </Route>

      <Route element={<ProtectedRoute roles={['student']} />}>
        <Route path="/profile" element={<StudentProfilePage />} />
        <Route path="/grades" element={<GradesPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
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
