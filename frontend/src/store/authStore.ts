import { create } from 'zustand'
import type { User } from '../api/auth'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isEmailVerified: boolean
  isLoading: boolean
  setUser: (user: User) => void
  clearUser: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isEmailVerified: false,
  isLoading: true,
  setUser: (user) => set({ user, isAuthenticated: true, isEmailVerified: user.is_email_verified, isLoading: false }),
  clearUser: () => set({ user: null, isAuthenticated: false, isEmailVerified: false, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
}))
