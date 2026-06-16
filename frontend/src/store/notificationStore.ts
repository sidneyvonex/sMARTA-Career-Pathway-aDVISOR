import { create } from 'zustand'

interface NotificationState {
  unreadCount: number
  drawerOpen: boolean
  setUnreadCount: (count: number) => void
  setDrawerOpen: (open: boolean) => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  unreadCount: 0,
  drawerOpen: false,
  setUnreadCount: (unreadCount) => set({ unreadCount }),
  setDrawerOpen: (drawerOpen) => set({ drawerOpen }),
}))
