import { useEffect } from 'react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser, clearUser } = useAuthStore()

  useEffect(() => {
    let cancelled = false
    authApi
      .me()
      .then((res) => {
        if (!cancelled) setUser(res.data.data.user)
      })
      .catch(() => {
        if (!cancelled) clearUser()
      })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { user, isAuthenticated, isLoading }
}
