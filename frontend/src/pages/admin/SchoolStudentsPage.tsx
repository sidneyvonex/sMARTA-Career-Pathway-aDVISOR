import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi, SchoolStudent } from '../../api/schoolAdmin'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import ErrorState from '../../components/common/dashboard/ErrorState'
import '../../styles/school-admin.css'

type Filter = 'all' | 'assigned' | 'unassigned' | 'assessed' | 'pending'

export default function SchoolStudentsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<Filter>('all')

  const studentsQ = useQuery({
    queryKey: ['school-admin', 'students'],
    queryFn: () => schoolAdminApi.getStudents().then(r => r.data.data),
  })

  const { downloadReport, downloadingId } = useDownloadReport()

  const counselorsQ = useQuery({
    queryKey: ['school-admin', 'counselors'],
    queryFn: () => schoolAdminApi.getCounselors().then(r => r.data.data),
  })
  const membershipRequestsQ = useQuery({
    queryKey: ['school-admin', 'membership-requests'],
    queryFn: () => schoolAdminApi.getMembershipRequests().then(r => r.data.data),
  })
  const students = studentsQ.data
  const counselors = counselorsQ.data

  const assignMutation = useMutation({
    mutationFn: ({ studentId, counselorId }: { studentId: number; counselorId: number }) =>
      schoolAdminApi.assignStudent(studentId, counselorId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      toast.success(res.data.message)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to assign student.')
    },
  })

  const decisionMutation = useMutation({
    mutationFn: ({
      studentId,
      decision,
    }: {
      studentId: number
      decision: 'approve' | 'reject'
    }) => schoolAdminApi.decideMembershipRequest(studentId, decision),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'membership-requests'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      toast.success(res.data.message)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Could not decide this school-link request.')
    },
  })

  if (studentsQ.isLoading || counselorsQ.isLoading) {
    return <p className="loading-text">Loading students…</p>
  }
  if (studentsQ.isError || counselorsQ.isError) {
    return (
      <ErrorState
        title="The student list could not load"
        description="Student and counsellor assignments are unchanged. Check your connection and try again."
        onRetry={() => {
          studentsQ.refetch()
          counselorsQ.refetch()
        }}
        actionLabel="Retry students"
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  const filtered = (students ?? []).filter((s: SchoolStudent) => {
    const matchesSearch =
      !search ||
      `${s.first_name} ${s.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
      s.email.toLowerCase().includes(search.toLowerCase())
    if (!matchesSearch) return false
    if (filter === 'assigned') return s.counselor_id !== null
    if (filter === 'unassigned') return s.counselor_id === null
    if (filter === 'assessed') return s.quiz_status === 'done'
    if (filter === 'pending') return s.quiz_status === 'pending'
    return true
  })

  function handleAssign(studentId: number, counselorId: number) {
    assignMutation.mutate({ studentId, counselorId })
  }

  const filters: { value: Filter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'assigned', label: 'Assigned' },
    { value: 'unassigned', label: 'Unassigned' },
    { value: 'assessed', label: 'Assessed' },
    { value: 'pending', label: 'Pending Assessment' },
  ]

  return (
    <div className="school-students-page">
      <h1>Students</h1>

      <section className="membership-queue" aria-labelledby="membership-queue-title">
        <div className="membership-queue__heading">
          <div>
            <p className="membership-queue__eyebrow">Identity and access</p>
            <h2 id="membership-queue-title">School-link approval requests</h2>
          </div>
          {!membershipRequestsQ.isLoading && !membershipRequestsQ.isError && (
            <span className="membership-queue__count">
              {membershipRequestsQ.data?.length ?? 0} pending
            </span>
          )}
        </div>
        <p className="membership-queue__notice">
          Confirm that each learner belongs to your school before approving access.
        </p>

        {membershipRequestsQ.isLoading ? (
          <p className="loading-text">Loading school-link requests…</p>
        ) : membershipRequestsQ.isError ? (
          <div className="membership-queue__error" role="alert">
            <p>School-link requests could not load.</p>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => membershipRequestsQ.refetch()}
            >
              Retry requests
            </button>
          </div>
        ) : membershipRequestsQ.data?.length ? (
          <div className="membership-queue__list">
            {membershipRequestsQ.data.map(request => {
              const name = `${request.first_name} ${request.last_name}`
              const decidingThisLearner = (
                decisionMutation.isPending
                && decisionMutation.variables?.studentId === request.student_id
              )
              return (
                <article className="membership-request-card" key={request.student_id}>
                  <div>
                    <h3>{name}</h3>
                    <p>{request.email}</p>
                    <span>Grade {request.grade}</span>
                  </div>
                  <div className="membership-request-card__actions">
                    <button
                      type="button"
                      className="btn-primary"
                      aria-label={`Approve ${name}`}
                      disabled={decisionMutation.isPending}
                      onClick={() => decisionMutation.mutate({
                        studentId: request.student_id,
                        decision: 'approve',
                      })}
                    >
                      {decidingThisLearner ? 'Saving…' : 'Approve'}
                    </button>
                    <button
                      type="button"
                      className="btn-ghost"
                      aria-label={`Reject ${name}`}
                      disabled={decisionMutation.isPending}
                      onClick={() => decisionMutation.mutate({
                        studentId: request.student_id,
                        decision: 'reject',
                      })}
                    >
                      Reject
                    </button>
                  </div>
                </article>
              )
            })}
          </div>
        ) : (
          <p className="membership-queue__empty">
            No school-link requests are waiting for review.
          </p>
        )}
      </section>

      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-4)', flexWrap: 'wrap' }}>
        <label htmlFor="student-search" className="sr-only">Search students</label>
        <input
          id="student-search"
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search students…"
          style={{ flex: 1, minWidth: '200px' }}
        />
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          {filters.map(f => (
            <button
              key={f.value}
              className={filter === f.value ? 'btn-primary' : 'btn-ghost'}
              onClick={() => setFilter(f.value)}
              style={{ fontSize: 'var(--font-size-sm)' }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="admin-empty-state">No students found.</p>
      ) : (
        <table className="counselor-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Grade</th>
              <th>Assessment</th>
              <th>Assigned Counselor</th>
              <th>Report</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(s => (
              <tr key={s.id}>
                <td>{s.first_name} {s.last_name}</td>
                <td>{s.grade}</td>
                <td>
                  <span className={`status-badge status-badge--${s.quiz_status === 'done' ? 'assessed' : 'pending'}`}>
                    {s.quiz_status === 'done' ? 'Done' : 'Pending'}
                  </span>
                </td>
                <td>
                  <select
                    className="assignment-select"
                    aria-label={`Assign counselor for ${s.first_name} ${s.last_name}`}
                    value={s.counselor_id ?? ''}
                    onChange={(e) => {
                      const val = e.target.value
                      if (val) handleAssign(s.id, Number(val))
                    }}
                    disabled={assignMutation.isPending || s.school_membership_status !== 'active'}
                  >
                    <option value="">Unassigned</option>
                    {counselors?.map(c => (
                      <option key={c.id} value={c.id}>
                        {c.first_name} {c.last_name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => downloadReport(s.id)}
                    disabled={downloadingId === s.id}
                    aria-label={`Download report for ${s.first_name} ${s.last_name}`}
                    style={{ minHeight: 'var(--min-touch-target)', padding: 'var(--space-1) var(--space-2)' }}
                  >
                    {downloadingId === s.id ? 'Generating…' : 'PDF'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
