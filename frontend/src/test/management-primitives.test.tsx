import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConfirmDialog from '../components/common/management/ConfirmDialog'
import DetailDrawer from '../components/common/management/DetailDrawer'
import ManagementTable from '../components/common/management/ManagementTable'
import ManagementToolbar from '../components/common/management/ManagementToolbar'
import ManagementPage from '../components/common/management/ManagementPage'
import Pagination from '../components/common/management/Pagination'
import RowActionMenu from '../components/common/management/RowActionMenu'
import type { ManagementAction, ManagementColumn } from '../components/common/management/types'

describe('management primitives', () => {
  it('opens an accessible row menu, orders danger actions last, and restores focus on Escape', async () => {
    const user = userEvent.setup()
    const edit = vi.fn()
    const remove = vi.fn()
    const actions: ManagementAction[] = [
      { id: 'remove', label: 'Remove', tone: 'danger', onSelect: remove },
      { id: 'edit', label: 'Edit', onSelect: edit },
    ]

    render(<RowActionMenu recordLabel="Grace Wanjiku" actions={actions} />)

    const trigger = screen.getByRole('button', {
      name: 'More actions for Grace Wanjiku',
    })
    await user.click(trigger)

    expect(screen.getByRole('menu')).toBeInTheDocument()
    expect(screen.getAllByRole('menuitem').map(item => item.textContent)).toEqual([
      'Edit',
      'Remove',
    ])

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('executes an action and closes when clicking outside', async () => {
    const user = userEvent.setup()
    const edit = vi.fn()

    render(
      <div>
        <RowActionMenu
          recordLabel="Daniel Otieno"
          actions={[{ id: 'edit', label: 'Edit', onSelect: edit }]}
        />
        <button type="button">Outside</button>
      </div>,
    )

    await user.click(screen.getByRole('button', { name: 'More actions for Daniel Otieno' }))
    await user.click(screen.getByRole('menuitem', { name: 'Edit' }))
    expect(edit).toHaveBeenCalledOnce()
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'More actions for Daniel Otieno' }))
    await user.click(screen.getByRole('button', { name: 'Outside' }))
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })

  it('renders an accessible confirmation dialog and protects pending work', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    const onClose = vi.fn()

    const { rerender } = render(
      <ConfirmDialog
        open
        title="Remove Grace Wanjiku?"
        description="Grace will no longer be available for learner assignments."
        confirmLabel="Remove counsellor"
        pending={false}
        onConfirm={onConfirm}
        onClose={onClose}
      />,
    )

    expect(screen.getByRole('dialog', { name: 'Remove Grace Wanjiku?' }))
      .toHaveAttribute('aria-modal', 'true')
    expect(document.body.style.overflow).toBe('hidden')
    await user.click(screen.getByRole('button', { name: 'Remove counsellor' }))
    expect(onConfirm).toHaveBeenCalledOnce()

    rerender(
      <ConfirmDialog
        open
        title="Remove Grace Wanjiku?"
        description="Grace will no longer be available for learner assignments."
        confirmLabel="Removing…"
        pending
        onConfirm={onConfirm}
        onClose={onClose}
      />,
    )
    expect(screen.getByRole('button', { name: 'Removing…' })).toBeDisabled()
    await user.keyboard('{Escape}')
    expect(onClose).not.toHaveBeenCalled()
  })

  it('closes a detail drawer on Escape and restores focus to its trigger', async () => {
    const user = userEvent.setup()

    function DrawerHarness() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>View workload</button>
          <DetailDrawer open={open} title="Grace Wanjiku workload" onClose={() => setOpen(false)}>
            <p>2 assigned learners</p>
          </DetailDrawer>
        </>
      )
    }

    render(<DrawerHarness />)
    const trigger = screen.getByRole('button', { name: 'View workload' })
    await user.click(trigger)
    expect(screen.getByRole('dialog', { name: 'Grace Wanjiku workload' })).toBeInTheDocument()
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
    expect(document.body.style.overflow).toBe('')
  })

  it('renders semantic management rows with mobile labels and coordinated actions', () => {
    const records = [
      { id: 1, name: 'Grace Wanjiku', email: 'grace@school.test', workload: 2 },
      { id: 2, name: 'Daniel Otieno', email: 'daniel@school.test', workload: 1 },
    ]
    const columns: ManagementColumn<(typeof records)[number]>[] = [
      {
        key: 'identity',
        label: 'Counsellor',
        priority: 'identity',
        render: record => <><strong>{record.name}</strong><span>{record.email}</span></>,
      },
      {
        key: 'workload',
        label: 'Workload',
        priority: 'essential',
        render: record => `${record.workload} learners`,
      },
    ]

    render(
      <ManagementTable
        ariaLabel="School counsellors"
        records={records}
        columns={columns}
        getKey={record => record.id}
        getRecordLabel={record => record.name}
        getPrimaryAction={record => ({
          id: 'view',
          label: `View ${record.name}`,
          onSelect: vi.fn(),
        })}
        getSecondaryActions={() => [{
          id: 'remove',
          label: 'Remove',
          tone: 'danger',
          onSelect: vi.fn(),
        }]}
        empty={<p>No counsellors</p>}
      />,
    )

    expect(screen.getByRole('table', { name: 'School counsellors' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Counsellor' })).toBeInTheDocument()
    expect(screen.getByText('grace@school.test').closest('td')).toHaveAttribute('data-label', 'Counsellor')
    expect(screen.getByText('2 learners').closest('td')).toHaveAttribute('data-priority', 'essential')
    expect(screen.getByRole('button', { name: 'View Grace Wanjiku' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'More actions for Grace Wanjiku' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'View Grace Wanjiku' }).closest('td')).toHaveAttribute('data-priority', 'action')
  })

  it('omits the overflow control when a row has no secondary actions', () => {
    const records = [{ id: 1, name: 'School created' }]
    const columns: ManagementColumn<(typeof records)[number]>[] = [{
      key: 'event',
      label: 'Event',
      priority: 'identity',
      render: record => record.name,
    }]

    render(
      <ManagementTable
        ariaLabel="Audit entries"
        records={records}
        columns={columns}
        getKey={record => record.id}
        getRecordLabel={record => record.name}
        getPrimaryAction={record => ({ id: 'view', label: `View ${record.name}`, onSelect: vi.fn() })}
        getSecondaryActions={() => []}
        empty={<p>No entries</p>}
      />,
    )

    expect(screen.getByRole('button', { name: 'View School created' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'More actions for School created' })).not.toBeInTheDocument()
  })

  it('coordinates labelled search, filters, page action, and live result count', () => {
    render(
      <ManagementToolbar
        resultCount="38 counsellors"
        search={(
          <label>
            <span>Search counsellors</span>
            <input type="search" />
          </label>
        )}
        filters={<button type="button">All workloads</button>}
        pageAction={<button type="button">Add counsellor</button>}
      />,
    )

    expect(screen.getByLabelText('Search counsellors')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'All workloads' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add counsellor' })).toBeInTheDocument()
    expect(screen.getByText('38 counsellors')).toHaveAttribute('aria-live', 'polite')
  })

  it('bounds pagination and reports page-size changes', async () => {
    const user = userEvent.setup()
    const onPageChange = vi.fn()
    const onPageSizeChange = vi.fn()

    const { rerender } = render(
      <Pagination
        state={{ page: 1, pageSize: 10, total: 38 }}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />,
    )

    expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled()
    expect(screen.getByText('Page 1 of 4')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Next page' }))
    expect(onPageChange).toHaveBeenCalledWith(2)
    await user.selectOptions(screen.getByLabelText('Rows per page'), '50')
    expect(onPageSizeChange).toHaveBeenCalledWith(50)

    rerender(
      <Pagination
        state={{ page: 4, pageSize: 10, total: 38 }}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />,
    )
    expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled()
  })

  it('composes a single-heading management page and its page action', () => {
    render(
      <ManagementPage
        eyebrow="School team"
        title="Counsellors"
        description="Review learner workloads."
        pageAction={<button type="button">Add counsellor</button>}
        toolbar={<div>Toolbar</div>}
        loading={false}
      >
        <p>Loaded counsellors</p>
      </ManagementPage>,
    )

    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('heading', { name: 'Counsellors', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add counsellor' })).toBeInTheDocument()
    expect(screen.getByText('Loaded counsellors')).toBeInTheDocument()
  })

  it('keeps loaded children out of initial loading and preserves retry on errors', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    const { rerender } = render(
      <ManagementPage title="Counsellors" description="Review learner workloads." loading>
        <p>Loaded counsellors</p>
      </ManagementPage>,
    )

    expect(screen.getByRole('status', { name: 'Loading Counsellors' })).toBeInTheDocument()
    expect(screen.queryByText('Loaded counsellors')).not.toBeInTheDocument()

    rerender(
      <ManagementPage
        title="Counsellors"
        description="Review learner workloads."
        loading={false}
        error={{ title: 'Counsellors could not load', description: 'Try again safely.' }}
        onRetry={onRetry}
      >
        <p>Loaded counsellors</p>
      </ManagementPage>,
    )
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })
})
