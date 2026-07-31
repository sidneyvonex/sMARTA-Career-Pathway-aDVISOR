import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DashboardHero from '../components/common/dashboard/DashboardHero'
import MetricCard from '../components/common/dashboard/MetricCard'
import SectionHeader from '../components/common/dashboard/SectionHeader'
import ActionCard from '../components/common/dashboard/ActionCard'
import StatusBadge from '../components/common/dashboard/StatusBadge'
import EmptyState from '../components/common/dashboard/EmptyState'
import ErrorState from '../components/common/dashboard/ErrorState'
import LoadingSkeleton from '../components/common/dashboard/LoadingSkeleton'
import ResponsiveDataList from '../components/common/dashboard/ResponsiveDataList'
import ActivityList from '../components/common/dashboard/ActivityList'

const renderWithRouter = (ui: React.ReactNode) =>
  render(<MemoryRouter>{ui}</MemoryRouter>)

describe('shared dashboard primitives', () => {
  it('renders a role-aware hero with labelled actions', () => {
    const onHelp = vi.fn()
    renderWithRouter(
      <DashboardHero
        tone="counsellor"
        eyebrow="Counsellor workspace"
        title="Good morning, Amina"
        description="Three learners need a follow-up."
        meta={['Kiambu County', '12 learners']}
        actions={[
          { label: 'Review learners', to: '/counselor/students' },
          { label: 'Open help', onClick: onHelp, variant: 'secondary' },
        ]}
      />,
    )

    expect(screen.getByRole('region', { name: 'Good morning, Amina' })).toHaveClass('db-hero--counsellor')
    expect(screen.getByRole('link', { name: 'Review learners' })).toHaveAttribute('href', '/counselor/students')
    fireEvent.click(screen.getByRole('button', { name: 'Open help' }))
    expect(onHelp).toHaveBeenCalledOnce()
  })

  it('supports static, linked, and interactive metrics', () => {
    const onSelect = vi.fn()
    renderWithRouter(
      <div>
        <MetricCard label="Learners" value={12} detail="Assigned to you" />
        <MetricCard label="Notes" value={8} to="/counselor/notes" />
        <MetricCard label="Follow-ups" value={3} tone="warning" onClick={onSelect} />
      </div>,
    )

    expect(screen.getByText('12')).toHaveClass('db-metric__value')
    expect(screen.getByRole('link', { name: /Notes: 8/i })).toHaveAttribute('href', '/counselor/notes')
    fireEvent.click(screen.getByRole('button', { name: /Follow-ups: 3/i }))
    expect(onSelect).toHaveBeenCalledOnce()
  })

  it('renders section and action-card navigation', () => {
    renderWithRouter(
      <>
        <SectionHeader
          eyebrow="Priority"
          title="This week"
          action={{ label: 'See all', to: '/tasks' }}
        />
        <ActionCard
          title="Review learner choices"
          description="Confirm the evidence before the counselling session."
          to="/tasks/choices"
          status={<StatusBadge tone="attention">Needs review</StatusBadge>}
        />
      </>,
    )

    expect(screen.getByRole('heading', { name: 'This week' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'See all' })).toHaveAttribute('href', '/tasks')
    expect(screen.getByRole('link', { name: /Review learner choices/i })).toHaveAttribute('href', '/tasks/choices')
    expect(screen.getByText('Needs review')).toHaveClass('db-status--attention')
  })

  it('provides actionable empty, error, and loading states', () => {
    const onRetry = vi.fn()
    renderWithRouter(
      <>
        <EmptyState
          title="No learners assigned"
          description="Assignments will appear here."
          action={{ label: 'View school', to: '/school' }}
        />
        <ErrorState
          title="Learners could not load"
          description="Check your connection and try again."
          onRetry={onRetry}
        />
        <LoadingSkeleton label="Loading learner dashboard" rows={2} />
      </>,
    )

    expect(screen.getByRole('link', { name: 'View school' })).toHaveAttribute('href', '/school')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledOnce()
    expect(screen.getByRole('status', { name: 'Loading learner dashboard' })).toBeInTheDocument()
  })

  it('renders a semantic data table with mobile cell labels', () => {
    const learners = [
      { id: 1, name: 'Wanjiku Njeri', status: 'Ready' },
      { id: 2, name: 'Brian Otieno', status: 'Follow-up' },
    ]

    render(
      <ResponsiveDataList
        ariaLabel="Assigned learners"
        items={learners}
        getKey={(learner) => learner.id}
        columns={[
          { key: 'name', label: 'Learner', render: (learner) => learner.name },
          { key: 'status', label: 'Status', render: (learner) => learner.status },
        ]}
      />,
    )

    expect(screen.getByRole('table', { name: 'Assigned learners' })).toBeInTheDocument()
    expect(screen.getByText('Wanjiku Njeri').closest('td')).toHaveAttribute('data-label', 'Learner')
    expect(screen.getByText('Follow-up').closest('td')).toHaveAttribute('data-label', 'Status')
  })

  it('renders activity as a labelled list with navigable items', () => {
    renderWithRouter(
      <ActivityList
        ariaLabel="Recent guidance activity"
        items={[
          {
            id: 1,
            title: 'Counsellor note added',
            detail: 'Review subject evidence before Friday.',
            time: '2 hours ago',
            to: '/notes/1',
          },
        ]}
      />,
    )

    expect(screen.getByRole('list', { name: 'Recent guidance activity' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Counsellor note added/i })).toHaveAttribute('href', '/notes/1')
    expect(screen.getByText('2 hours ago')).toBeInTheDocument()
  })
})
