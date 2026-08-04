import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
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

const roleUsers = {
  student: { ...counselor, role: 'student' as const },
  counselor,
  school_admin: { ...counselor, role: 'school_admin' as const },
  system_admin: { ...counselor, role: 'system_admin' as const },
  parent: { ...counselor, role: 'parent' as const },
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
      mobileMoreOpen: false,
    })
    useNotificationStore.setState({ unreadCount: 0, drawerOpen: false })
    Object.defineProperty(window.navigator, 'onLine', {
      configurable: true,
      value: true,
    })
  })

  afterEach(() => {
    document.body.style.overflow = ''
    vi.unstubAllEnvs()
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

  it('uses the progress title and breadcrumb when the academic progress flag is on', () => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'true')
    useAuthStore.setState({ user: roleUsers.student })

    renderShell('/grades')

    expect(screen.getByText('My progress', { selector: '.topbar__greeting-main' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('My progress')
  })

  it('exposes education goals only while the academic progress rollout is on', () => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'true')
    useAuthStore.setState({ user: roleUsers.student })

    const { unmount } = renderShell('/education-goals')

    expect(screen.getByRole('link', { name: 'Education Goals' })).toHaveAttribute(
      'href', '/education-goals',
    )
    expect(screen.getByText('Education goals', { selector: '.topbar__greeting-main' })).toBeInTheDocument()
    unmount()

    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'false')
    renderShell('/education-goals')
    expect(screen.queryByRole('link', { name: 'Education Goals' })).not.toBeInTheDocument()
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
    useLayoutStore.setState({ mobileSidebarOpen: true, mobileMoreOpen: true })
    renderShell()

    const moreDialog = screen.getByRole('dialog', { name: 'More navigation and account' })
    await userEvent.click(within(moreDialog).getByRole('button', { name: 'Log out' }))

    await waitFor(() => {
      expect(useLayoutStore.getState().mobileSidebarOpen).toBe(false)
      expect(useLayoutStore.getState().mobileMoreOpen).toBe(false)
    })
  })

  it.each([
    ['student', ['Home', 'Grades', 'Explore', 'Plan', 'More']],
    ['counselor', ['Home', 'Students', 'Notes', 'More']],
    ['school_admin', ['Dashboard', 'Learners', 'Offerings', 'Team', 'More']],
    ['system_admin', ['Home', 'Schools', 'Catalogue', 'Users', 'More']],
  ] as const)('renders the approved %s phone destinations', (role, labels) => {
    vi.stubEnv('VITE_ACADEMIC_PROGRESS_V1', 'false')
    useAuthStore.setState({ user: roleUsers[role] })
    renderShell()

    const navigation = screen.getByRole('navigation', { name: 'Mobile primary navigation' })
    expect(navigation).toBeInTheDocument()
    expect(Array.from(navigation.querySelectorAll('a, button')).map((item) => item.textContent)).toEqual(labels)
  })

  it('uses the first linked learner as the parent phone destination', async () => {
    useAuthStore.setState({ user: roleUsers.parent })
    renderShell()

    const navigation = screen.getByRole('navigation', { name: 'Mobile primary navigation' })
    expect(within(navigation).getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(await within(navigation).findByRole('link', { name: 'Tom' })).toHaveAttribute('href', '/parent/child/10')
    expect(within(navigation).getByRole('button', { name: 'More' })).toBeInTheDocument()
    expect(navigation).toHaveStyle({ '--bottom-nav-count': '3' })
  })

  it('dismisses the More sheet on Escape and restores focus to its trigger', async () => {
    renderShell()
    const more = screen.getByRole('button', { name: 'More' })

    await userEvent.click(more)
    expect(screen.getByRole('dialog', { name: 'More navigation and account' })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Close More menu' })).toHaveLength(1)
    expect(more).toHaveClass('active')

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog', { name: 'More navigation and account' })).not.toBeInTheDocument()
    expect(more).toHaveFocus()
  })

  it('closes the More sheet after navigating', async () => {
    useAuthStore.setState({ user: roleUsers.student })
    renderShell()

    await userEvent.click(screen.getByRole('button', { name: 'More' }))
    const dialog = screen.getByRole('dialog', { name: 'More navigation and account' })
    await userEvent.click(within(dialog).getByRole('link', { name: 'Compare Choices' }))

    expect(screen.queryByRole('dialog', { name: 'More navigation and account' })).not.toBeInTheDocument()
  })

  it('closes the More sheet when the viewport changes to tablet navigation', async () => {
    let handleViewportChange: ((event: MediaQueryListEvent) => void) | undefined
    const mediaQuery = vi.spyOn(window, 'matchMedia').mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: (_type: string, listener: EventListenerOrEventListenerObject) => {
        handleViewportChange = listener as (event: MediaQueryListEvent) => void
      },
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))
    renderShell()
    await userEvent.click(screen.getByRole('button', { name: 'More' }))

    act(() => handleViewportChange?.({ matches: true } as MediaQueryListEvent))

    expect(screen.queryByRole('dialog', { name: 'More navigation and account' })).not.toBeInTheDocument()
    expect(document.body.style.overflow).toBe('')
    mediaQuery.mockRestore()
  })

  it('marks only the most specific More destination as current', async () => {
    useAuthStore.setState({ user: roleUsers.student })
    renderShell('/assessment/results')

    await userEvent.click(screen.getByRole('button', { name: 'More' }))
    const dialog = screen.getByRole('dialog', { name: 'More navigation and account' })
    const currentLinks = within(dialog).getAllByRole('link', { current: 'page' })

    expect(currentLinks).toHaveLength(1)
    expect(currentLinks[0]).toHaveTextContent('Career Profile')
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
