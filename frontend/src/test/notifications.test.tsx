import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { useNotificationStore } from '../store/notificationStore'
import { useAuthStore } from '../store/authStore'
import { useNotificationPoll } from '../hooks/useNotificationPoll'
import Topbar from '../components/shell/Topbar'
import Sidebar from '../components/shell/Sidebar'
import NotificationPanel from '../components/shell/NotificationPanel'

function makeWrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client }, children)
  }
}

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

describe('useNotificationPoll', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    useNotificationStore.setState({ unreadCount: 0, drawerOpen: false })
    useAuthStore.setState({ isAuthenticated: true, user: null, isEmailVerified: false, isLoading: false })
  })

  afterEach(() => {
    qc.clear()
  })

  it('sets unreadCount from API response', async () => {
    renderHook(() => useNotificationPoll(), { wrapper: makeWrapper(qc) })
    await waitFor(() => {
      expect(useNotificationStore.getState().unreadCount).toBe(1)
    })
  })

  it('does not fire a toast on initial load', async () => {
    const { default: toast } = await import('react-hot-toast')
    const toastFn = vi.mocked(toast.success)
    toastFn.mockClear()
    renderHook(() => useNotificationPoll(), { wrapper: makeWrapper(qc) })
    await waitFor(() => {
      expect(useNotificationStore.getState().unreadCount).toBe(1)
    })
    expect(toastFn).not.toHaveBeenCalled()
  })
})

describe('Topbar / Sidebar', () => {
  const mockUser = {
    id: 1, email: 'test@example.com', first_name: 'Alice', last_name: 'Doe',
    role: 'student' as const, is_email_verified: true,
  }

  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isEmailVerified: false, isLoading: false })
    useNotificationStore.setState({ unreadCount: 0, drawerOpen: false })
  })

  it('renders the brand name in Sidebar', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, isEmailVerified: true, isLoading: false })
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    )
    expect(screen.getByText('Smarta Shauri')).toBeInTheDocument()
  })

  it('shows no badge when unreadCount is 0', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, isEmailVerified: true, isLoading: false })
    render(
      <MemoryRouter>
        <Topbar />
      </MemoryRouter>
    )
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('shows badge with count when unreadCount > 0', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, isEmailVerified: true, isLoading: false })
    useNotificationStore.setState({ unreadCount: 3, drawerOpen: false })
    render(
      <MemoryRouter>
        <Topbar />
      </MemoryRouter>
    )
    expect(screen.getByRole('status')).toHaveTextContent('3')
  })

  it('opens drawer when bell is clicked', async () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, isEmailVerified: true, isLoading: false })
    render(
      <MemoryRouter>
        <Topbar />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: /notifications/i }))
    expect(useNotificationStore.getState().drawerOpen).toBe(true)
  })
})

describe('NotificationPanel', () => {
  let qc: QueryClient

  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    useNotificationStore.setState({ drawerOpen: false, unreadCount: 0 })
  })

  afterEach(() => {
    qc.clear()
  })

  function renderDrawer(open: boolean) {
    useNotificationStore.setState({ drawerOpen: open, unreadCount: 0 })
    return render(
      createElement(QueryClientProvider, { client: qc },
        createElement(NotificationPanel)
      )
    )
  }

  it('is hidden when closed', () => {
    renderDrawer(false)
    const drawer = document.querySelector('.notification-drawer')
    expect(drawer).not.toHaveClass('open')
  })

  it('is visible when open', () => {
    renderDrawer(true)
    const drawer = document.querySelector('.notification-drawer')
    expect(drawer).toHaveClass('open')
  })

  it('shows notification messages when open', async () => {
    renderDrawer(true)
    expect(await screen.findByText('Your RIASEC assessment results are ready.')).toBeInTheDocument()
  })

  it('closes when close button is clicked', async () => {
    renderDrawer(true)
    await userEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(useNotificationStore.getState().drawerOpen).toBe(false)
  })

  it('shows "Mark all as read" button when there are unread notifications', async () => {
    renderDrawer(true)
    expect(await screen.findByRole('button', { name: /mark all as read/i })).toBeInTheDocument()
  })

  it('fires toast.success on mark-all success', async () => {
    const toastMod = await import('react-hot-toast')
    const successFn = vi.mocked(toastMod.default.success)
    successFn.mockClear()
    renderDrawer(true)
    await userEvent.click(await screen.findByRole('button', { name: /mark all as read/i }))
    await waitFor(() => {
      expect(successFn).toHaveBeenCalledWith('All notifications marked as read.')
    })
  })
})
