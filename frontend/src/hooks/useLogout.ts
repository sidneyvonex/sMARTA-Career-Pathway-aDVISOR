import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { clearUserScopedStorage } from '../lib/sessionCleanup'
import { useAuthStore } from '../store/authStore'
import { useLayoutStore } from '../store/layoutStore'

export function useLogout() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const clearUser = useAuthStore((state) => state.clearUser)
  const resetTransientNavigation = useLayoutStore((state) => state.resetTransientNavigation)

  return async () => {
    try {
      await authApi.logout()
    } catch {
      // Local session cleanup still runs when the server cannot be reached.
    }
    queryClient.clear()
    clearUserScopedStorage()
    resetTransientNavigation()
    clearUser()
    navigate('/login')
    toast.success('Logged out.')
  }
}
