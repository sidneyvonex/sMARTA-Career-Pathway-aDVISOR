import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { useNotificationStore } from '../store/notificationStore'
import { useAuthStore } from '../store/authStore'
import { useNotificationPoll } from '../hooks/useNotificationPoll'
import Navbar from '../components/layout/Navbar'

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

describe('Navbar', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isEmailVerified: false, isLoading: false })
    useNotificationStore.setState({ unreadCount: 0, drawerOpen: false })
  })

  it('renders the brand name', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    )
    expect(screen.getByText('Smarta Shauri')).toBeInTheDocument()
  })

  it('shows no badge when unreadCount is 0', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    )
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('shows badge with count when unreadCount > 0', () => {
    useNotificationStore.setState({ unreadCount: 3, drawerOpen: false })
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    )
    expect(screen.getByRole('status')).toHaveTextContent('3')
  })

  it('opens drawer when bell is clicked', async () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: /notifications/i }))
    expect(useNotificationStore.getState().drawerOpen).toBe(true)
  })
})
