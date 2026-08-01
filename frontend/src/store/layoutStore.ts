import { create } from 'zustand'

interface LayoutState {
  sidebarCollapsed: boolean
  mobileSidebarOpen: boolean
  mobileMoreOpen: boolean
  toggleSidebar: () => void
  setMobileSidebarOpen: (open: boolean) => void
  setMobileMoreOpen: (open: boolean) => void
  resetTransientNavigation: () => void
}

export const useLayoutStore = create<LayoutState>((set) => ({
  sidebarCollapsed: false,
  mobileSidebarOpen: false,
  mobileMoreOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
  setMobileMoreOpen: (open) => set({ mobileMoreOpen: open }),
  resetTransientNavigation: () => set({ mobileSidebarOpen: false, mobileMoreOpen: false }),
}))
