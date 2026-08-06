import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { systemAdminApi, type SchoolItem } from '../../api/systemAdmin'
import ConfirmDialog from '../../components/common/management/ConfirmDialog'
import DetailDrawer from '../../components/common/management/DetailDrawer'
import ManagementPage from '../../components/common/management/ManagementPage'
import ManagementTable from '../../components/common/management/ManagementTable'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import EmptyState from '../../components/common/dashboard/EmptyState'
import type { ManagementColumn } from '../../components/common/management/types'
import { ALL_ROLLOUT_COUNTIES, ROLLOUT_COUNTIES } from '../../lib/rollout'
import '../../styles/system-admin.css'

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'true', label: 'Active' },
  { value: 'false', label: 'Inactive' },
]

function formatCounty(county: string): string {
  if (county === 'muranga') return "Murang'a"
  return county.charAt(0).toUpperCase() + county.slice(1)
}

function evidenceLabel(school: SchoolItem) {
  if (school.verification_status === 'verified') return 'Verified'
  if (school.verification_status === 'demonstration') return 'Demonstration'
  return 'Not verified'
}

export default function SystemAdminSchoolsPage() {
  const queryClient = useQueryClient()
  const [county, setCounty] = useState('')
  const [search, setSearch] = useState('')
  const [active, setActive] = useState('')
  const [page, setPage] = useState(1)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingSchool, setEditingSchool] = useState<SchoolItem | null>(null)
  const [detailSchool, setDetailSchool] = useState<SchoolItem | null>(null)
  const [statusSchool, setStatusSchool] = useState<SchoolItem | null>(null)
  const [transferSchool, setTransferSchool] = useState<SchoolItem | null>(null)
  const [transferEmail, setTransferEmail] = useState('')
  const [confirmingTransfer, setConfirmingTransfer] = useState<{ schoolId: number; email: string } | null>(null)
  const [editData, setEditData] = useState({ name: '', phone: '', email: '' })
  const [createData, setCreateData] = useState({
    name: '',
    county: '',
    school_code: '',
    phone: '',
    email: '',
  })

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['system-admin', 'schools', { county, search, active, page }],
    queryFn: () => systemAdminApi.getSchools({
      ...(county && { county }),
      ...(search && { search }),
      ...(active && { active }),
      page,
    }).then(response => response.data.data),
  })

  const invalidateSchools = () => {
    queryClient.invalidateQueries({ queryKey: ['system-admin', 'schools'] })
    queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
  }

  const createMutation = useMutation({
    mutationFn: (formData: typeof createData) => systemAdminApi.createSchool({
      name: formData.name,
      county: formData.county,
      school_code: formData.school_code,
      ...(formData.phone && { phone: formData.phone }),
      ...(formData.email && { email: formData.email }),
    }),
    onSuccess: () => {
      invalidateSchools()
      toast.success(`${createData.name} created. Login details sent to ${createData.email}.`)
      setCreateData({ name: '', county: '', school_code: '', phone: '', email: '' })
      setShowCreateForm(false)
    },
    onError: (error: any) => {
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to create school.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: typeof editData }) => (
      systemAdminApi.updateSchool(id, values)
    ),
    onSuccess: () => {
      invalidateSchools()
      toast.success('School updated.')
      setEditingSchool(null)
    },
    onError: (error: any) => {
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to update school.')
    },
  })

  const statusMutation = useMutation({
    mutationFn: (school: SchoolItem) => (
      school.is_active
        ? systemAdminApi.deactivateSchool(school.id)
        : systemAdminApi.activateSchool(school.id)
    ),
    onSuccess: (_, school) => {
      invalidateSchools()
      toast.success(school.is_active ? 'School deactivated.' : 'School activated.')
      setStatusSchool(null)
    },
    onError: (error: any) => {
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to update school status.')
    },
  })

  const transferMutation = useMutation({
    mutationFn: async ({ schoolId, email }: { schoolId: number; email: string }) => {
      const lookup = await systemAdminApi.getUsers({ search: email })
      const match = lookup.data.data.results.find(u => u.email.toLowerCase() === email.toLowerCase())
      if (!match) throw new Error('NOT_FOUND')
      return systemAdminApi.transferSchoolAdmin(schoolId, match.id)
    },
    onSuccess: (response) => {
      invalidateSchools()
      toast.success(response.data.message)
      setTransferSchool(null)
      setTransferEmail('')
      setConfirmingTransfer(null)
    },
    onError: (error: any) => {
      setConfirmingTransfer(null)
      if (error?.message === 'NOT_FOUND') {
        toast.error('No user found with that email.')
        return
      }
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to transfer admin.')
    },
  })

  useEffect(() => {
    if (isError) toast.error('Failed to load schools.')
  }, [isError])

  const schools = data?.results ?? []
  const total = data?.total ?? 0
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const columns: ManagementColumn<SchoolItem>[] = [
    {
      key: 'school',
      label: 'School',
      priority: 'identity',
      render: school => (
        <div className="admin-person">
          <strong>{school.name}</strong>
          <span>{school.school_code ?? 'Code not recorded'}</span>
        </div>
      ),
    },
    {
      key: 'county',
      label: 'County',
      priority: 'essential',
      render: school => formatCounty(school.county),
    },
    {
      key: 'learners',
      label: 'Learners',
      priority: 'essential',
      align: 'end',
      render: school => <span className="management-number">{school.student_count}</span>,
    },
    {
      key: 'counsellors',
      label: 'Counsellors',
      priority: 'secondary',
      align: 'end',
      render: school => <span className="management-number">{school.counselor_count}</span>,
    },
    {
      key: 'evidence',
      label: 'Evidence',
      priority: 'secondary',
      render: school => (
        <span className={`sysadmin-badge sysadmin-badge--${school.verification_status === 'verified' ? 'active' : 'inactive'}`}>
          {evidenceLabel(school)}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      priority: 'essential',
      render: school => (
        <span className={`sysadmin-badge sysadmin-badge--${school.is_active ? 'active' : 'inactive'}`}>
          {school.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  function startEdit(school: SchoolItem) {
    setEditingSchool(school)
    setEditData({ name: school.name, phone: school.phone || '', email: school.email || '' })
  }

  const createForm = showCreateForm ? (
    <form className="sysadmin-create-form" onSubmit={(event: FormEvent) => {
      event.preventDefault()
      createMutation.mutate(createData)
    }}>
      <div className="sysadmin-create-form__heading">
        <div>
          <h2>Create a pilot school</h2>
          <p>Add the school identity first. Contact details can be completed now or updated later.</p>
        </div>
        <button type="button" className="btn-ghost" onClick={() => setShowCreateForm(false)}>Close form</button>
      </div>
      <div className="sysadmin-create-form__grid">
        <div className="form-field">
          <label htmlFor="create-name">School name</label>
          <input id="create-name" value={createData.name} onChange={event => setCreateData(value => ({ ...value, name: event.target.value }))} required />
        </div>
        <div className="form-field">
          <label htmlFor="create-county">County</label>
          <select id="create-county" value={createData.county} onChange={event => setCreateData(value => ({ ...value, county: event.target.value }))} required>
            <option value="">Select county</option>
            {ROLLOUT_COUNTIES.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="create-code">School code</label>
          <input id="create-code" value={createData.school_code} onChange={event => setCreateData(value => ({ ...value, school_code: event.target.value }))} required />
        </div>
        <div className="form-field">
          <label htmlFor="create-phone">Phone</label>
          <input id="create-phone" type="tel" value={createData.phone} onChange={event => setCreateData(value => ({ ...value, phone: event.target.value }))} />
        </div>
        <div className="form-field">
          <label htmlFor="create-email">Email</label>
          <input id="create-email" type="email" value={createData.email} onChange={event => setCreateData(value => ({ ...value, email: event.target.value }))} required />
          <p className="form-hint">Used to create the school's login account. A temporary password will be emailed here.</p>
        </div>
      </div>
      <div className="sysadmin-create-form__actions">
        <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
          {createMutation.isPending ? 'Creating…' : 'Create school'}
        </button>
        <button type="button" className="btn-ghost" onClick={() => setShowCreateForm(false)} disabled={createMutation.isPending}>Cancel</button>
      </div>
    </form>
  ) : null

  const editForm = editingSchool ? (
    <form className="sysadmin-create-form" onSubmit={(event: FormEvent) => {
      event.preventDefault()
      updateMutation.mutate({ id: editingSchool.id, values: editData })
    }}>
      <div className="sysadmin-create-form__heading">
        <div>
          <h2>Edit {editingSchool.name}</h2>
          <p>Update the school name and contact details. County and school code remain system controlled.</p>
        </div>
      </div>
      <div className="sysadmin-create-form__grid">
        <div className="form-field">
          <label htmlFor="edit-school-name">School name</label>
          <input id="edit-school-name" value={editData.name} onChange={event => setEditData(value => ({ ...value, name: event.target.value }))} required />
        </div>
        <div className="form-field">
          <label htmlFor="edit-school-phone">Phone</label>
          <input id="edit-school-phone" type="tel" value={editData.phone} onChange={event => setEditData(value => ({ ...value, phone: event.target.value }))} />
        </div>
        <div className="form-field">
          <label htmlFor="edit-school-email">Email</label>
          <input id="edit-school-email" type="email" value={editData.email} onChange={event => setEditData(value => ({ ...value, email: event.target.value }))} />
        </div>
      </div>
      <div className="sysadmin-create-form__actions">
        <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>{updateMutation.isPending ? 'Saving…' : 'Save changes'}</button>
        <button type="button" className="btn-ghost" onClick={() => setEditingSchool(null)} disabled={updateMutation.isPending}>Cancel</button>
      </div>
    </form>
  ) : null

  const toolbar = (
    <ManagementToolbar
      resultCount={`${total} school${total === 1 ? '' : 's'}`}
      search={(
        <label htmlFor="school-search">
          <span>Search schools</span>
          <input id="school-search" type="search" value={search} onChange={event => { setSearch(event.target.value); setPage(1) }} placeholder="Name or school code" />
        </label>
      )}
      filters={(
        <>
          <label htmlFor="school-county">
            <span>County</span>
            <select id="school-county" value={county} onChange={event => { setCounty(event.target.value); setPage(1) }}>
              {ALL_ROLLOUT_COUNTIES.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label htmlFor="school-status">
            <span>Status</span>
            <select id="school-status" value={active} onChange={event => { setActive(event.target.value); setPage(1) }}>
              {STATUS_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
        </>
      )}
    />
  )

  return (
    <>
      <ManagementPage
        eyebrow="Five-county rollout"
        title="Schools"
        description="Review pilot schools, operational coverage, evidence status, and access."
        pageAction={(
          <button type="button" className="btn-primary" onClick={() => { setShowCreateForm(value => !value); setEditingSchool(null) }}>
            {showCreateForm ? 'Close create form' : 'Create school'}
          </button>
        )}
        toolbar={toolbar}
        loading={isLoading}
        error={isError ? { title: 'Schools could not load', description: 'No school records were changed. Check your connection and try again.' } : undefined}
        onRetry={() => refetch()}
      >
        {createForm}
        {editForm}
        <ManagementTable
          ariaLabel="Pilot schools"
          records={schools}
          columns={columns}
          getKey={school => school.id}
          getRecordLabel={school => school.name}
          getPrimaryAction={school => ({ id: 'view', label: `View ${school.name}`, shortLabel: 'View', onSelect: () => setDetailSchool(school) })}
          getSecondaryActions={school => [
            { id: 'edit', label: 'Edit', disabled: statusMutation.isPending, onSelect: () => { setShowCreateForm(false); startEdit(school) } },
            { id: 'status', label: school.is_active ? 'Deactivate' : 'Activate', tone: school.is_active ? 'danger' : 'default', disabled: statusMutation.isPending, onSelect: () => setStatusSchool(school) },
          ]}
          empty={<EmptyState title="No schools found" description="Try changing the county, status, or search term." />}
        />
        {totalPages > 1 && (
          <nav className="sysadmin-pagination" aria-label="School pages">
            <button type="button" className="btn-ghost" onClick={() => setPage(value => Math.max(1, value - 1))} disabled={page <= 1}>Previous</button>
            <span aria-live="polite">Page {page} of {totalPages}</span>
            <button type="button" className="btn-ghost" onClick={() => setPage(value => Math.min(totalPages, value + 1))} disabled={page >= totalPages}>Next</button>
          </nav>
        )}
      </ManagementPage>

      <DetailDrawer open={detailSchool !== null} title={detailSchool ? `${detailSchool.name} details` : 'School details'} onClose={() => setDetailSchool(null)}>
        {detailSchool && (
          <dl className="sysadmin-detail-list">
            <div><dt>School code</dt><dd>{detailSchool.school_code ?? 'Not recorded'}</dd></div>
            <div><dt>County</dt><dd>{formatCounty(detailSchool.county)}</dd></div>
            <div><dt>Email</dt><dd>{detailSchool.email || 'Not recorded'}</dd></div>
            <div><dt>Phone</dt><dd>{detailSchool.phone || 'Not recorded'}</dd></div>
            <div><dt>Learners</dt><dd>{detailSchool.student_count}</dd></div>
            <div><dt>Counsellors</dt><dd>{detailSchool.counselor_count}</dd></div>
            <div><dt>Evidence</dt><dd>{evidenceLabel(detailSchool)}</dd></div>
            <div><dt>Status</dt><dd>{detailSchool.is_active ? 'Active' : 'Inactive'}</dd></div>
          </dl>
        )}
        {detailSchool && (
          <button type="button" className="btn-ghost" onClick={() => { setTransferSchool(detailSchool); setTransferEmail(''); setDetailSchool(null) }}>
            Transfer admin
          </button>
        )}
      </DetailDrawer>

      {transferSchool && (
        <form
          className="sysadmin-create-form"
          onSubmit={(event: FormEvent) => {
            event.preventDefault()
            if (!transferEmail.trim()) return
            setConfirmingTransfer({ schoolId: transferSchool.id, email: transferEmail.trim() })
          }}
        >
          <div className="sysadmin-create-form__heading">
            <div>
              <h2>Transfer admin for {transferSchool.name}</h2>
              <p>Enter the email of the existing account to make the new school admin. They'll be promoted if needed, and the outgoing admin will be unlinked from this school.</p>
            </div>
            <button type="button" className="btn-ghost" onClick={() => setTransferSchool(null)}>Close form</button>
          </div>
          <div className="form-field">
            <label htmlFor="transfer-admin-email">New admin email</label>
            <input id="transfer-admin-email" type="email" value={transferEmail} onChange={event => setTransferEmail(event.target.value)} required />
          </div>
          <div className="sysadmin-create-form__actions">
            <button type="submit" className="btn-primary" disabled={transferMutation.isPending}>
              {transferMutation.isPending ? 'Transferring…' : 'Transfer'}
            </button>
          </div>
        </form>
      )}

      <ConfirmDialog
        open={statusSchool !== null}
        title={statusSchool ? `${statusSchool.is_active ? 'Deactivate' : 'Activate'} ${statusSchool.name}?` : 'Change school status?'}
        description={statusSchool?.is_active
          ? `${statusSchool.name} will stop accepting administrative activity until it is activated again.`
          : `${statusSchool?.name ?? 'This school'} will regain access to school administration.`}
        confirmLabel={statusMutation.isPending ? 'Updating…' : statusSchool?.is_active ? 'Deactivate school' : 'Activate school'}
        pending={statusMutation.isPending}
        onClose={() => setStatusSchool(null)}
        onConfirm={() => { if (statusSchool) statusMutation.mutate(statusSchool) }}
      />

      <ConfirmDialog
        open={confirmingTransfer !== null}
        title={transferSchool ? `Transfer admin for ${transferSchool.name} to ${confirmingTransfer?.email}?` : 'Transfer admin?'}
        description="This changes who administers the school. The outgoing admin will lose access, and the new admin will be promoted if they aren't already staff."
        confirmLabel={transferMutation.isPending ? 'Transferring…' : 'Transfer admin'}
        pending={transferMutation.isPending}
        onClose={() => setConfirmingTransfer(null)}
        onConfirm={() => { if (confirmingTransfer) transferMutation.mutate(confirmingTransfer) }}
      />
    </>
  )
}
