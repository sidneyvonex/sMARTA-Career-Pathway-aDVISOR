import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { systemAdminApi, SchoolItem } from '../../api/systemAdmin'
import '../../styles/system-admin.css'

const COUNTIES = [
  { value: '', label: 'All Counties' },
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
]

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'true', label: 'Active' },
  { value: 'false', label: 'Inactive' },
]

function formatCounty(county: string): string {
  if (county === 'muranga') return "Murang'a"
  return county.charAt(0).toUpperCase() + county.slice(1)
}

export default function SystemAdminSchoolsPage() {
  const queryClient = useQueryClient()

  // Filter state
  const [county, setCounty] = useState('')
  const [search, setSearch] = useState('')
  const [active, setActive] = useState('')
  const [page, setPage] = useState(1)

  // UI state
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editData, setEditData] = useState<{ name: string; phone: string; email: string }>({ name: '', phone: '', email: '' })

  // Create form state
  const [createData, setCreateData] = useState({
    name: '',
    county: '',
    school_code: '',
    phone: '',
    email: '',
  })

  // Query
  const { data, isLoading, isError } = useQuery({
    queryKey: ['system-admin', 'schools', { county, search, active, page }],
    queryFn: () =>
      systemAdminApi
        .getSchools({
          ...(county && { county }),
          ...(search && { search }),
          ...(active && { active }),
          page,
        })
        .then(r => r.data.data),
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: (formData: typeof createData) =>
      systemAdminApi.createSchool({
        name: formData.name,
        county: formData.county,
        school_code: formData.school_code,
        ...(formData.phone && { phone: formData.phone }),
        ...(formData.email && { email: formData.email }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'schools'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success('School created successfully.')
      setCreateData({ name: '', county: '', school_code: '', phone: '', email: '' })
      setShowCreateForm(false)
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Failed to create school.'
      toast.error(msg)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; phone?: string; email?: string } }) =>
      systemAdminApi.updateSchool(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'schools'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success('School updated.')
      setEditingId(null)
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Failed to update school.'
      toast.error(msg)
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => systemAdminApi.deactivateSchool(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'schools'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success('School deactivated.')
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Failed to deactivate school.'
      toast.error(msg)
    },
  })

  const activateMutation = useMutation({
    mutationFn: (id: number) => systemAdminApi.activateSchool(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'schools'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success('School activated.')
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Failed to activate school.'
      toast.error(msg)
    },
  })

  // Handlers
  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate(createData)
  }

  function startEdit(school: SchoolItem) {
    setEditingId(school.id)
    setEditData({ name: school.name, phone: school.phone || '', email: school.email || '' })
  }

  function cancelEdit() {
    setEditingId(null)
  }

  function handleUpdate(id: number) {
    updateMutation.mutate({ id, data: editData })
  }

  function handleToggleActive(school: SchoolItem) {
    if (school.is_active) {
      deactivateMutation.mutate(school.id)
    } else {
      activateMutation.mutate(school.id)
    }
  }

  const isMutating = createMutation.isPending || updateMutation.isPending || deactivateMutation.isPending || activateMutation.isPending

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="sysadmin-page">
        <div className="skeleton" style={{ height: 40, width: '60%', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-5)' }} />
        <div className="skeleton" style={{ height: 44, width: '100%', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)' }} />
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="skeleton" style={{ height: 48, width: '100%', marginBottom: 'var(--space-2)', borderRadius: 'var(--radius-sm)' }} />
        ))}
      </div>
    )
  }

  // Error state
  if (isError) {
    toast.error('Failed to load schools.')
    return (
      <div className="sysadmin-page">
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          Something went wrong loading schools. Please try again.
        </p>
      </div>
    )
  }

  const schools = data?.results ?? []
  const total = data?.total ?? 0
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="sysadmin-page">
      {/* Header */}
      <div className="sysadmin-page__header">
        <h1 className="sysadmin-dashboard__title">Schools</h1>
        <button
          className="btn-primary"
          style={{ minHeight: 'var(--min-touch-target)' }}
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancel' : 'Create School'}
        </button>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <form className="sysadmin-create-form" onSubmit={handleCreate}>
          <div className="sysadmin-create-form__grid">
            <div className="form-field">
              <label htmlFor="create-name">School Name *</label>
              <input
                id="create-name"
                type="text"
                value={createData.name}
                onChange={e => setCreateData(d => ({ ...d, name: e.target.value }))}
                required
                style={{ minHeight: 'var(--min-touch-target)' }}
              />
            </div>
            <div className="form-field">
              <label htmlFor="create-county">County *</label>
              <select
                id="create-county"
                value={createData.county}
                onChange={e => setCreateData(d => ({ ...d, county: e.target.value }))}
                required
                style={{ minHeight: 'var(--min-touch-target)' }}
              >
                <option value="">Select county</option>
                {COUNTIES.filter(c => c.value).map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="create-code">School Code *</label>
              <input
                id="create-code"
                type="text"
                value={createData.school_code}
                onChange={e => setCreateData(d => ({ ...d, school_code: e.target.value }))}
                required
                style={{ minHeight: 'var(--min-touch-target)' }}
              />
            </div>
            <div className="form-field">
              <label htmlFor="create-phone">Phone</label>
              <input
                id="create-phone"
                type="tel"
                value={createData.phone}
                onChange={e => setCreateData(d => ({ ...d, phone: e.target.value }))}
                style={{ minHeight: 'var(--min-touch-target)' }}
              />
            </div>
            <div className="form-field">
              <label htmlFor="create-email">Email</label>
              <input
                id="create-email"
                type="email"
                value={createData.email}
                onChange={e => setCreateData(d => ({ ...d, email: e.target.value }))}
                style={{ minHeight: 'var(--min-touch-target)' }}
              />
            </div>
          </div>
          <div className="sysadmin-create-form__actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={createMutation.isPending}
              style={{ minHeight: 'var(--min-touch-target)' }}
            >
              {createMutation.isPending ? 'Creating...' : 'Create School'}
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => setShowCreateForm(false)}
              style={{ minHeight: 'var(--min-touch-target)' }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Filters */}
      <div className="sysadmin-filters">
        <label htmlFor="filter-county" className="sr-only">Filter by county</label>
        <select
          id="filter-county"
          value={county}
          onChange={e => { setCounty(e.target.value); setPage(1) }}
        >
          {COUNTIES.map(c => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>

        <label htmlFor="filter-search" className="sr-only">Search schools</label>
        <input
          id="filter-search"
          type="search"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search schools..."
        />

        <label htmlFor="filter-status" className="sr-only">Filter by status</label>
        <select
          id="filter-status"
          value={active}
          onChange={e => { setActive(e.target.value); setPage(1) }}
        >
          {STATUS_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {schools.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          No schools found.
        </p>
      ) : (
        <table className="sysadmin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>County</th>
              <th>Code</th>
              <th>Students</th>
              <th>Counselors</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {schools.map(school => (
              <tr key={school.id}>
                {editingId === school.id ? (
                  <>
                    <td>
                      <label htmlFor={`edit-name-${school.id}`} className="sr-only">School name</label>
                      <input
                        id={`edit-name-${school.id}`}
                        type="text"
                        value={editData.name}
                        onChange={e => setEditData(d => ({ ...d, name: e.target.value }))}
                        style={{ minHeight: 'var(--min-touch-target)', width: '100%' }}
                      />
                    </td>
                    <td>{formatCounty(school.county)}</td>
                    <td>{school.school_code}</td>
                    <td>{school.student_count}</td>
                    <td>{school.counselor_count}</td>
                    <td>
                      <span className={`sysadmin-badge sysadmin-badge--${school.is_active ? 'active' : 'inactive'}`}>
                        {school.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                      <button
                        className="sysadmin-action-btn"
                        onClick={() => handleUpdate(school.id)}
                        disabled={isMutating}
                      >
                        {updateMutation.isPending ? 'Saving...' : 'Save'}
                      </button>
                      <button
                        className="sysadmin-action-btn"
                        onClick={cancelEdit}
                        disabled={isMutating}
                      >
                        Cancel
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{school.name}</td>
                    <td>{formatCounty(school.county)}</td>
                    <td>{school.school_code}</td>
                    <td>{school.student_count}</td>
                    <td>{school.counselor_count}</td>
                    <td>
                      <span className={`sysadmin-badge sysadmin-badge--${school.is_active ? 'active' : 'inactive'}`}>
                        {school.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                      <button
                        className="sysadmin-action-btn"
                        onClick={() => startEdit(school)}
                        disabled={isMutating}
                      >
                        Edit
                      </button>
                      <button
                        className={`sysadmin-action-btn ${school.is_active ? 'sysadmin-action-btn--danger' : ''}`}
                        onClick={() => handleToggleActive(school)}
                        disabled={isMutating}
                      >
                        {school.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="sysadmin-pagination">
          <button
            className="sysadmin-action-btn"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Previous
          </button>
          <span>Page {page} of {totalPages}</span>
          <button
            className="sysadmin-action-btn"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
