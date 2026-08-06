import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { systemAdminApi, type UserItem } from '../../api/systemAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ConfirmDialog from '../../components/common/management/ConfirmDialog'
import DetailDrawer from '../../components/common/management/DetailDrawer'
import ManagementPage from '../../components/common/management/ManagementPage'
import ManagementTable from '../../components/common/management/ManagementTable'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import type { ManagementColumn } from '../../components/common/management/types'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import { ALL_ROLLOUT_COUNTIES } from '../../lib/rollout'
import '../../styles/system-admin.css'

const ROLE_OPTIONS = [
  { value: '', label: 'All roles' },
  { value: 'student', label: 'Student' },
  { value: 'counselor', label: 'Counsellor' },
  { value: 'school_admin', label: 'School administrator' },
  { value: 'parent', label: 'Parent' },
  { value: 'system_admin', label: 'System administrator' },
]

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'true', label: 'Active' },
  { value: 'false', label: 'Inactive' },
]

function formatCounty(county: string | null): string {
  if (!county) return 'Not assigned'
  if (county === 'muranga') return "Murang'a"
  return county.charAt(0).toUpperCase() + county.slice(1)
}

function formatRole(role: string): string {
  if (role === 'counselor') return 'Counsellor'
  return role.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' })
}

function userName(user: UserItem) {
  return `${user.first_name} ${user.last_name}`
}

export default function SystemAdminUsersPage() {
  const queryClient = useQueryClient()
  const { downloadStudentReport, downloadingId } = useDownloadReport()
  const [role, setRole] = useState('')
  const [county, setCounty] = useState('')
  const [school, setSchool] = useState('')
  const [search, setSearch] = useState('')
  const [active, setActive] = useState('')
  const [page, setPage] = useState(1)
  const [detailUser, setDetailUser] = useState<UserItem | null>(null)
  const [statusUser, setStatusUser] = useState<UserItem | null>(null)
  const [resetUser, setResetUser] = useState<UserItem | null>(null)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['system-admin', 'users', { role, county, school, search, active, page }],
    queryFn: () => systemAdminApi.getUsers({
      ...(role && { role }),
      ...(county && { county }),
      ...(school && { school }),
      ...(search && { search }),
      ...(active && { active }),
      page,
    }).then(response => response.data.data),
  })

  const { data: schoolsData } = useQuery({
    queryKey: ['system-admin', 'schools-list'],
    queryFn: () => systemAdminApi.getSchools({ page: 1 }).then(response => response.data.data.results),
  })

  const statusMutation = useMutation({
    mutationFn: (user: UserItem) => (
      user.is_active
        ? systemAdminApi.deactivateUser(user.id)
        : systemAdminApi.activateUser(user.id)
    ),
    onSuccess: (_, user) => {
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'users'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      toast.success(user.is_active ? 'User deactivated.' : 'User activated.')
      setStatusUser(null)
    },
    onError: (error: any) => {
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to update user status.')
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: (user: UserItem) => systemAdminApi.resetUserPassword(user.id),
    onSuccess: (response) => {
      toast.success(response.data.message)
      setResetUser(null)
    },
    onError: (error: any) => {
      const message = error.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Failed to reset password.')
    },
  })

  useEffect(() => {
    if (isError) toast.error('Failed to load users.')
  }, [isError])

  const users = data?.results ?? []
  const total = data?.total ?? 0
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const schools = schoolsData ?? []

  const columns: ManagementColumn<UserItem>[] = [
    {
      key: 'user',
      label: 'User',
      priority: 'identity',
      render: user => (
        <div className="admin-person">
          <strong>{userName(user)}</strong>
          <span title={user.email}>{user.email}</span>
        </div>
      ),
    },
    {
      key: 'role',
      label: 'Role',
      priority: 'essential',
      render: user => <span className={`sysadmin-role-badge sysadmin-role-badge--${user.role}`}>{formatRole(user.role)}</span>,
    },
    {
      key: 'affiliation',
      label: 'School or county',
      priority: 'essential',
      render: user => (
        <div className="admin-person">
          <strong>{user.school_name ?? formatCounty(user.county)}</strong>
          {user.school_name && <span>{formatCounty(user.county)}</span>}
        </div>
      ),
    },
    {
      key: 'verification',
      label: 'Verification',
      priority: 'secondary',
      render: user => (
        <span className={`sysadmin-badge sysadmin-badge--${user.is_email_verified ? 'active' : 'inactive'}`}>
          {user.is_email_verified ? 'Verified' : 'Unverified'}
        </span>
      ),
    },
    {
      key: 'joined',
      label: 'Joined',
      priority: 'secondary',
      render: user => formatDate(user.created_at),
    },
    {
      key: 'status',
      label: 'Status',
      priority: 'essential',
      render: user => (
        <span className={`sysadmin-badge sysadmin-badge--${user.is_active ? 'active' : 'inactive'}`}>
          {user.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  const toolbar = (
    <ManagementToolbar
      resultCount={`${total} user${total === 1 ? '' : 's'}`}
      search={(
        <label htmlFor="user-search">
          <span>Search users</span>
          <input id="user-search" type="search" value={search} onChange={event => { setSearch(event.target.value); setPage(1) }} placeholder="Name or email" />
        </label>
      )}
      filters={(
        <>
          <label htmlFor="user-role">
            <span>Role</span>
            <select id="user-role" value={role} onChange={event => { setRole(event.target.value); setPage(1) }}>
              {ROLE_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label htmlFor="user-county">
            <span>County</span>
            <select id="user-county" value={county} onChange={event => { setCounty(event.target.value); setPage(1) }}>
              {ALL_ROLLOUT_COUNTIES.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <label htmlFor="user-school">
            <span>School</span>
            <select id="user-school" value={school} onChange={event => { setSchool(event.target.value); setPage(1) }}>
              <option value="">All schools</option>
              {schools.map(option => <option key={option.id} value={String(option.id)}>{option.name}</option>)}
            </select>
          </label>
          <label htmlFor="user-status">
            <span>Status</span>
            <select id="user-status" value={active} onChange={event => { setActive(event.target.value); setPage(1) }}>
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
        eyebrow="Platform access"
        title="Users"
        description="Review role, affiliation, verification, and account status without exposing unnecessary account metadata."
        toolbar={toolbar}
        loading={isLoading}
        error={isError ? { title: 'Users could not load', description: 'No user records were changed. Check your connection and try again.' } : undefined}
        onRetry={() => refetch()}
      >
        <ManagementTable
          ariaLabel="Platform users"
          records={users}
          columns={columns}
          getKey={user => user.id}
          getRecordLabel={userName}
          getPrimaryAction={user => ({ id: 'view', label: `View ${userName(user)}`, shortLabel: 'View', onSelect: () => setDetailUser(user) })}
          getSecondaryActions={user => [
            ...(user.role === 'student' ? [{
              id: 'download',
              label: 'Download PDF',
              disabled: downloadingId === user.id,
              onSelect: () => downloadStudentReport(user.id),
            }] : []),
            {
              id: 'reset-password',
              label: 'Reset password',
              disabled: resetPasswordMutation.isPending,
              onSelect: () => setResetUser(user),
            },
            {
              id: 'status',
              label: user.is_active ? 'Deactivate' : 'Activate',
              tone: user.is_active ? 'danger' as const : 'default' as const,
              disabled: statusMutation.isPending,
              onSelect: () => setStatusUser(user),
            },
          ]}
          empty={<EmptyState title="No users found" description="Try changing the role, school, county, status, or search term." />}
        />
        {totalPages > 1 && (
          <nav className="sysadmin-pagination" aria-label="User pages">
            <button type="button" className="btn-ghost" onClick={() => setPage(value => Math.max(1, value - 1))} disabled={page <= 1}>Previous</button>
            <span aria-live="polite">Page {page} of {totalPages}</span>
            <button type="button" className="btn-ghost" onClick={() => setPage(value => Math.min(totalPages, value + 1))} disabled={page >= totalPages}>Next</button>
          </nav>
        )}
      </ManagementPage>

      <DetailDrawer open={detailUser !== null} title={detailUser ? `${userName(detailUser)} details` : 'User details'} onClose={() => setDetailUser(null)}>
        {detailUser && (
          <dl className="sysadmin-detail-list">
            <div><dt>Email</dt><dd>{detailUser.email}</dd></div>
            <div><dt>Role</dt><dd>{formatRole(detailUser.role)}</dd></div>
            <div><dt>School</dt><dd>{detailUser.school_name ?? 'Not assigned'}</dd></div>
            <div><dt>County</dt><dd>{formatCounty(detailUser.county)}</dd></div>
            <div><dt>Email verification</dt><dd>{detailUser.is_email_verified ? 'Verified' : 'Unverified'}</dd></div>
            <div><dt>Joined</dt><dd>{formatDate(detailUser.created_at)}</dd></div>
            <div><dt>Status</dt><dd>{detailUser.is_active ? 'Active' : 'Inactive'}</dd></div>
          </dl>
        )}
      </DetailDrawer>

      <ConfirmDialog
        open={statusUser !== null}
        title={statusUser ? `${statusUser.is_active ? 'Deactivate' : 'Activate'} ${userName(statusUser)}?` : 'Change user status?'}
        description={statusUser?.is_active
          ? `${userName(statusUser)} will lose platform access until the account is activated again.`
          : `${statusUser ? userName(statusUser) : 'This user'} will regain platform access.`}
        confirmLabel={statusMutation.isPending ? 'Updating…' : statusUser?.is_active ? 'Deactivate user' : 'Activate user'}
        pending={statusMutation.isPending}
        onClose={() => setStatusUser(null)}
        onConfirm={() => { if (statusUser) statusMutation.mutate(statusUser) }}
      />

      <ConfirmDialog
        open={resetUser !== null}
        title={resetUser ? `Reset password for ${userName(resetUser)}?` : 'Reset password?'}
        description={resetUser
          ? `${userName(resetUser)} will receive a new temporary password by email and should sign in with it.`
          : 'A new temporary password will be emailed to this user.'}
        confirmLabel={resetPasswordMutation.isPending ? 'Resetting…' : 'Reset password'}
        pending={resetPasswordMutation.isPending}
        onClose={() => setResetUser(null)}
        onConfirm={() => { if (resetUser) resetPasswordMutation.mutate(resetUser) }}
      />
    </>
  )
}
