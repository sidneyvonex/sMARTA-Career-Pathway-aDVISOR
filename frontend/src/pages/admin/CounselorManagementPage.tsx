import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi, type SchoolCounselor } from '../../api/schoolAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ConfirmDialog from '../../components/common/management/ConfirmDialog'
import DetailDrawer from '../../components/common/management/DetailDrawer'
import ManagementPage from '../../components/common/management/ManagementPage'
import ManagementTable from '../../components/common/management/ManagementTable'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import type { ManagementColumn } from '../../components/common/management/types'
import '../../styles/dashboard.css'
import '../../styles/school-admin.css'

const getCounsellorName = (counsellor: SchoolCounselor) => (
  `${counsellor.first_name} ${counsellor.last_name}`
)

export default function CounselorManagementPage() {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [search, setSearch] = useState('')
  const [detailCounsellor, setDetailCounsellor] = useState<SchoolCounselor | null>(null)
  const [removingCounsellor, setRemovingCounsellor] = useState<SchoolCounselor | null>(null)

  const { data: counsellors, isLoading, isError, refetch } = useQuery({
    queryKey: ['school-admin', 'counselors'],
    queryFn: () => schoolAdminApi.getCounselors().then(response => response.data.data),
  })

  const addMutation = useMutation({
    mutationFn: (value: string) => schoolAdminApi.addCounselor(value),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      toast.success(response.data.message)
      setEmail('')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message ?? 'Failed to add counsellor.')
    },
  })

  const removeMutation = useMutation({
    mutationFn: (id: number) => schoolAdminApi.removeCounselor(id),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      toast.success(response.data.message)
      setRemovingCounsellor(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message ?? 'Failed to remove counsellor.')
    },
  })

  const normalizedSearch = search.trim().toLowerCase()
  const filtered = useMemo(() => (counsellors ?? []).filter(counsellor => (
    !normalizedSearch
    || getCounsellorName(counsellor).toLowerCase().includes(normalizedSearch)
    || counsellor.email.toLowerCase().includes(normalizedSearch)
  )), [counsellors, normalizedSearch])

  const columns: ManagementColumn<SchoolCounselor>[] = [
    {
      key: 'identity',
      label: 'Counsellor',
      priority: 'identity',
      render: counsellor => (
        <div className="admin-person">
          <strong>{getCounsellorName(counsellor)}</strong>
          <span>{counsellor.email}</span>
        </div>
      ),
    },
    {
      key: 'workload',
      label: 'Workload',
      priority: 'essential',
      render: counsellor => (
        <span className="admin-workload">
          {counsellor.student_count} learner{counsellor.student_count === 1 ? '' : 's'}
        </span>
      ),
    },
    {
      key: 'joined',
      label: 'Joined',
      priority: 'secondary',
      render: counsellor => new Date(counsellor.joined_at).toLocaleDateString(),
    },
  ]

  function handleAdd(event: React.FormEvent) {
    event.preventDefault()
    if (email.trim()) addMutation.mutate(email.trim())
  }

  const inviteForm = (
    <form onSubmit={handleAdd} className="counsellor-invite-form">
      <label htmlFor="counselor-email" className="sr-only">Counselor email</label>
      <input
        id="counselor-email"
        type="email"
        value={email}
        onChange={event => setEmail(event.target.value)}
        placeholder="Counselor email address"
        required
      />
      <button type="submit" className="btn-primary" disabled={addMutation.isPending}>
        {addMutation.isPending ? 'Adding…' : 'Add Counselor'}
      </button>
    </form>
  )

  const toolbar = (
    <ManagementToolbar
      resultCount={`${filtered.length} counsellor${filtered.length === 1 ? '' : 's'}`}
      search={(
        <label htmlFor="counsellor-search">
          <span>Search counsellors</span>
          <input
            id="counsellor-search"
            type="search"
            value={search}
            onChange={event => setSearch(event.target.value)}
            placeholder="Search by name or email"
          />
        </label>
      )}
    />
  )

  return (
    <>
      <ManagementPage
        eyebrow="School team"
        title="Counsellors"
        description="Invite counsellors and keep learner workloads visible before making assignments."
        pageAction={inviteForm}
        toolbar={toolbar}
        loading={isLoading}
        error={isError ? {
          title: 'The counsellor list could not load',
          description: 'No counsellor records were changed. Check your connection and try again.',
        } : undefined}
        onRetry={() => refetch()}
        errorActionLabel="Retry counsellors"
      >
        <ManagementTable
          ariaLabel="School counsellors"
          records={filtered}
          columns={columns}
          getKey={counsellor => counsellor.id}
          getRecordLabel={getCounsellorName}
          getPrimaryAction={counsellor => ({
            id: 'view-workload',
            label: `View workload for ${getCounsellorName(counsellor)}`,
            onSelect: () => setDetailCounsellor(counsellor),
          })}
          getSecondaryActions={counsellor => [{
            id: 'remove',
            label: 'Remove',
            tone: 'danger',
            disabled: removeMutation.isPending,
            onSelect: () => setRemovingCounsellor(counsellor),
          }]}
          empty={(
            <EmptyState
              title={search ? 'No matching counsellors' : 'No counsellors yet'}
              description={search
                ? 'Try a different name or email.'
                : 'Add a verified counsellor by email to begin assigning learners.'}
            />
          )}
        />
      </ManagementPage>

      <DetailDrawer
        open={detailCounsellor !== null}
        title={detailCounsellor ? `${getCounsellorName(detailCounsellor)} workload` : 'Counsellor workload'}
        onClose={() => setDetailCounsellor(null)}
      >
        {detailCounsellor && (
          <dl className="counsellor-workload-details">
            <div>
              <dt>Email</dt>
              <dd>{detailCounsellor.email}</dd>
            </div>
            <div>
              <dt>Assigned learners</dt>
              <dd>{detailCounsellor.student_count} assigned learners</dd>
            </div>
            <div>
              <dt>Joined</dt>
              <dd>{new Date(detailCounsellor.joined_at).toLocaleDateString()}</dd>
            </div>
          </dl>
        )}
      </DetailDrawer>

      <ConfirmDialog
        open={removingCounsellor !== null}
        title={removingCounsellor ? `Remove ${getCounsellorName(removingCounsellor)}?` : 'Remove counsellor?'}
        description={removingCounsellor
          ? `${getCounsellorName(removingCounsellor)} will no longer be available for learner assignments.`
          : 'This counsellor will no longer be available for learner assignments.'}
        confirmLabel={removeMutation.isPending ? 'Removing…' : 'Remove counsellor'}
        pending={removeMutation.isPending}
        onClose={() => setRemovingCounsellor(null)}
        onConfirm={() => {
          if (removingCounsellor) removeMutation.mutate(removingCounsellor.id)
        }}
      />
    </>
  )
}
