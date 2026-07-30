import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi, type SchoolCounselor } from '../../api/schoolAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ErrorState from '../../components/common/dashboard/ErrorState'
import ResponsiveDataList, { type DataColumn } from '../../components/common/dashboard/ResponsiveDataList'
import SectionHeader from '../../components/common/dashboard/SectionHeader'
import '../../styles/dashboard.css'
import '../../styles/school-admin.css'

export default function CounselorManagementPage() {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [search, setSearch] = useState('')
  const [removingId, setRemovingId] = useState<number | null>(null)

  const { data: counselors, isLoading, isError, refetch } = useQuery({
    queryKey: ['school-admin', 'counselors'],
    queryFn: () => schoolAdminApi.getCounselors().then(r => r.data.data),
  })

  const addMutation = useMutation({
    mutationFn: (value: string) => schoolAdminApi.addCounselor(value),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      toast.success(res.data.message)
      setEmail('')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to add counselor.')
    },
  })

  const removeMutation = useMutation({
    mutationFn: (id: number) => schoolAdminApi.removeCounselor(id),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      toast.success(res.data.message)
      setRemovingId(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to remove counselor.')
      setRemovingId(null)
    },
  })

  function handleAdd(event: React.FormEvent) {
    event.preventDefault()
    if (email.trim()) addMutation.mutate(email.trim())
  }

  function handleRemove(id: number) {
    if (removingId === id) {
      removeMutation.mutate(id)
    } else {
      setRemovingId(id)
    }
  }

  if (isLoading) return <p className="loading-text">Loading counsellors…</p>
  if (isError) {
    return (
      <ErrorState
        title="The counsellor list could not load"
        description="No counsellor records were changed. Check your connection and try again."
        onRetry={() => refetch()}
        actionLabel="Retry counsellors"
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  const normalizedSearch = search.trim().toLowerCase()
  const filtered = (counselors ?? []).filter(counselor => (
    !normalizedSearch
    || `${counselor.first_name} ${counselor.last_name}`.toLowerCase().includes(normalizedSearch)
    || counselor.email.toLowerCase().includes(normalizedSearch)
  ))
  const columns: DataColumn<SchoolCounselor>[] = [
    {
      key: 'name',
      label: 'Counsellor',
      render: counselor => (
        <div className="admin-person">
          <strong>{counselor.first_name} {counselor.last_name}</strong>
          <span>{counselor.email}</span>
        </div>
      ),
    },
    {
      key: 'workload',
      label: 'Workload',
      render: counselor => (
        <span className="admin-workload">
          {counselor.student_count} learner{counselor.student_count === 1 ? '' : 's'}
        </span>
      ),
    },
    {
      key: 'joined',
      label: 'Joined',
      render: counselor => new Date(counselor.joined_at).toLocaleDateString(),
    },
    {
      key: 'actions',
      label: 'Action',
      align: 'end',
      render: counselor => (
        <button
          type="button"
          className="btn-ghost"
          onClick={() => handleRemove(counselor.id)}
          disabled={removeMutation.isPending}
          style={removingId === counselor.id ? { color: 'var(--color-error)' } : undefined}
        >
          {removingId === counselor.id ? 'Confirm Remove' : 'Remove'}
        </button>
      ),
    },
  ]

  return (
    <div className="counselor-management-page">
      <SectionHeader
        eyebrow="School team"
        title="Counselors"
        description="Invite counsellors and keep learner workloads visible before making assignments."
      />

      <form onSubmit={handleAdd} className="counselor-management-page__add-form">
        <label htmlFor="counselor-email" className="sr-only">Counselor email</label>
        <input
          id="counselor-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Counselor email address"
          required
        />
        <button type="submit" className="btn-primary" disabled={addMutation.isPending}>
          {addMutation.isPending ? 'Adding…' : 'Add Counselor'}
        </button>
      </form>

      <label className="admin-search">
        <span>Search counsellors</span>
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by name or email"
        />
      </label>

      <ResponsiveDataList
        ariaLabel="School counsellors"
        items={filtered}
        columns={columns}
        getKey={counselor => counselor.id}
        empty={(
          <EmptyState
            title={search ? 'No matching counsellors' : 'No counsellors yet'}
            description={search
              ? 'Try a different name or email.'
              : 'Add a verified counsellor by email to begin assigning learners.'}
          />
        )}
      />
    </div>
  )
}
