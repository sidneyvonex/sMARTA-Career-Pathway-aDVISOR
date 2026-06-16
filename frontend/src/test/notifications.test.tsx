import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createElement } from 'react'
import { useNotificationStore } from '../store/notificationStore'
import { useNotificationPoll } from '../hooks/useNotificationPoll'

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
