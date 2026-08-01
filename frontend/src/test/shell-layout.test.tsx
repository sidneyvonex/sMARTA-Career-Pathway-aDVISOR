import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Shell from '../components/shell/Shell'
import { useAuthStore } from '../store/authStore'
import { useLayoutStore } from '../store/layoutStore'
import { useNotificationStore } from '../store/notificationStore'

const counselor = {
  id: 8,
  email: 'amina@example.com',
  first_name: 'Amina',
  last_name: 'Otieno',
  role: 'counselor' as const,
  is_email_verified: true,
  county: 'kisumu',
}

function renderShell(path = '/') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Shell>
          <div>Page content</div>
        </Shell>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('authenticated shell layout', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: counselor,
      isAuthenticated: true,
      isEmailVerified: true,
      isLoading: false,
    })
    useLayoutStore.setState({
      sidebarCollapsed: false,
      mobileSidebarOpen: false,
    })
    useNotificationStore.setState({ unreadCount: 0, drawerOpen: false })
    Object.defineProperty(window.navigator, 'onLine', {
      configurable: true,
      value: true,
    })
  })

  afterEach(() => {
    document.body.style.overflow = ''
  })

  it('provides route-aware title and breadcrumb context', () => {
    renderShell('/counselor/students/42')

    expect(screen.getByText('Learner details', { selector: '.topbar__greeting-main' })).toBeInTheDocument()
    const breadcrumbs = screen.getByRole('navigation', { name: 'Breadcrumb' })
    expect(breadcrumbs).toHaveTextContent('My students')
    expect(breadcrumbs).toHaveTextContent('Learner details')
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Open account home' })).toBeInTheDocument()
  })

  it('starts keyboard navigation with the skip link and then the sidebar control', async () => {
    const user = userEvent.setup()
    renderShell()

    const skipLink = screen.getByRole('link', { name: 'Skip to main content' })
    await user.tab()
    expect(skipLink).toHaveFocus()

    await user.tab()
    expect(screen.getByRole('button', { name: 'Collapse sidebar' })).toHaveFocus()
  })

  it('opens and closes mobile navigation with an announced expanded state', async () => {
    renderShell('/counselor/students')
    const openButton = screen.getByRole('button', { name: 'Open navigation' })

    expect(openButton).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(openButton)

    expect(openButton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByLabelText('Main navigation')).toHaveClass('sidebar--mobile-open')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Close navigation' })).toHaveFocus()
    })

    await userEvent.keyboard('{Escape}')
    expect(openButton).toHaveAttribute('aria-expanded', 'false')
    expect(openButton).toHaveFocus()

    await userEvent.click(openButton)
    await userEvent.click(screen.getByRole('button', { name: 'Close navigation' }))
    expect(openButton).toHaveAttribute('aria-expanded', 'false')
    expect(openButton).toHaveFocus()
  })

  it('closes transient mobile navigation when the user logs out', async () => {
    useLayoutStore.setState({ mobileSidebarOpen: true })
    renderShell()

    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))

    await waitFor(() => {
      expect(useLayoutStore.getState().mobileSidebarOpen).toBe(false)
    })
  })

  it('wraps page content in the shared authenticated content container', () => {
    renderShell()

    expect(screen.getByTestId('shell-content-inner')).toHaveTextContent('Page content')
  })

  it('announces when the browser is offline', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      configurable: true,
      value: false,
    })

    renderShell()

    expect(screen.getByRole('status')).toHaveTextContent(
      'Offline. Saved pages may remain available, but updates need a connection.',
    )
  })

  it('keeps the closed notification drawer out of the accessibility and layout trees', () => {
    renderShell()

    expect(screen.queryByRole('dialog', { name: 'Notifications' })).not.toBeInTheDocument()
  })
})
