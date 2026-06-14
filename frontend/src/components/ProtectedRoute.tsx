import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import type { User } from '../api/auth'

interface Props {
  roles?: User['role'][]
}

export default function ProtectedRoute({ roles }: Props) {
  const { user, isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading…</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
