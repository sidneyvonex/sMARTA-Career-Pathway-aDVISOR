import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { systemAdminApi, UserItem } from '../../api/systemAdmin'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import '../../styles/system-admin.css'

const COUNTIES = [
  { value: '', label: 'All Counties' },
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
]

const ROLE_OPTIONS = [
  { value: '', label: 'All Roles' },
  { value: 'student', label: 'Student' },
  { value: 'counselor', label: 'Counselor' },
  { value: 'school_admin', label: 'School Admin' },
  { value: 'parent', label: 'Parent' },
  { value: 'system_admin', label: 'System Admin' },
]

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'true', label: 'Active' },
  { value: 'false', label: 'Inactive' },
]

function formatCounty(county: string | null): string {
  if (!county) return '—'
  if (county === 'muranga') return "Murang'a"
  return county.charAt(0).toUpperCase() + county.slice(1)
}

function formatRole(role: string): string {
  return role
    .split('_')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function SystemAdminUsersPage() {
  const queryClient = useQueryClient()

  const { downloadReport, downloadingId } = useDownloadReport()

  // Filter state
  const [role, setRole] = useState('')
  const [county, setCounty] = useState('')
  const [school, setSchool] = useState('')
  const [search, setSearch] = useState('')
  const [active, setActive] = useState('')
  const [page, setPage] = useState(1)

  // Users query
  const { data, isLoading, isError } = useQuery({
    queryKey: ['system-admin', 'users', { role, county, school, search, active, page }],
    queryFn: () =>
      systemAdminApi
        .getUsers({
          ...(role && { role }),
          ...(county && { county }),
          ...(school && { school }),
          ...(search && { search }),
          ...(active && { active }),
          page,
        })
        .then(r => r.data.data),
  })

  // Schools query (for filter dropdown)
  const { data: schoolsData } = useQuery({
    queryKey: ['system-admin', 'schools-list'],
    queryFn: () =>
      systemAdminApi
        .getSchools({ page: 1 })
        .then(r => r.data.data.results),
  })

  // Mutations
  const deactivateMutation = useMutation({
    mutationFn: (id: number) => systemAdminApi.deactivateUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success('User deactivated.')
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Failed to deactivate user.'
      toast.error(msg)
    },
  })

  const activateMutation = useMutation({
    mutationFn: (id: number) => systemAdminApi.activateUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success('User activated.')
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Failed to activate user.'
      toast.error(msg)
    },
  })

  function handleToggleActive(user: UserItem) {
    if (user.is_active) {
      deactivateMutation.mutate(user.id)
    } else {
      activateMutation.mutate(user.id)
    }
  }

  const isMutating = deactivateMutation.isPending || activateMutation.isPending

  useEffect(() => {
    if (isError) toast.error('Failed to load users.')
  }, [isError])

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

  if (isError) {
    return (
      <div className="sysadmin-page">
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          Something went wrong loading users. Please try again.
        </p>
      </div>
    )
  }

  const users = data?.results ?? []
  const total = data?.total ?? 0
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.ceil(total / pageSize)
  const schools = schoolsData ?? []

  return (
    <div className="sysadmin-page">
      {/* Header */}
      <div className="sysadmin-page__header">
        <h1 className="sysadmin-dashboard__title">Users</h1>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          {total} user{total !== 1 ? 's' : ''} total
        </span>
      </div>

      {/* Filters */}
      <div className="sysadmin-filters">
        <label htmlFor="filter-role" className="sr-only">Filter by role</label>
        <select
          id="filter-role"
          value={role}
          onChange={e => { setRole(e.target.value); setPage(1) }}
        >
          {ROLE_OPTIONS.map(r => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>

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

        <label htmlFor="filter-school" className="sr-only">Filter by school</label>
        <select
          id="filter-school"
          value={school}
          onChange={e => { setSchool(e.target.value); setPage(1) }}
        >
          <option value="">All Schools</option>
          {schools.map(s => (
            <option key={s.id} value={String(s.id)}>{s.name}</option>
          ))}
        </select>

        <label htmlFor="filter-search" className="sr-only">Search users</label>
        <input
          id="filter-search"
          type="search"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search by name or email..."
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
      {users.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          No users found.
        </p>
      ) : (
        <table className="sysadmin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>County</th>
              <th>School</th>
              <th>Verified</th>
              <th>Status</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>{user.first_name} {user.last_name}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`sysadmin-role-badge sysadmin-role-badge--${user.role}`}>
                    {formatRole(user.role)}
                  </span>
                </td>
                <td>{formatCounty(user.county)}</td>
                <td>{user.school_name ?? '—'}</td>
                <td>{user.is_email_verified ? '✓' : '✗'}</td>
                <td>
                  <span className={`sysadmin-badge sysadmin-badge--${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{formatDate(user.created_at)}</td>
                <td>
                  <button
                    className={`sysadmin-action-btn ${user.is_active ? 'sysadmin-action-btn--danger' : ''}`}
                    onClick={() => handleToggleActive(user)}
                    disabled={isMutating}
                  >
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  {user.role === 'student' && (
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => downloadReport(user.id)}
                      disabled={downloadingId === user.id}
                      aria-label={`Download report for ${user.first_name} ${user.last_name}`}
                      style={{ minHeight: 'var(--min-touch-target)', padding: 'var(--space-1) var(--space-2)', marginLeft: 'var(--space-2)' }}
                    >
                      {downloadingId === user.id ? 'Generating…' : 'PDF'}
                    </button>
                  )}
                </td>
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
