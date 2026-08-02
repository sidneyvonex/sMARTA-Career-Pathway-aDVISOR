import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi, type SchoolStudent } from '../../api/schoolAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ErrorState from '../../components/common/dashboard/ErrorState'
import ResponsiveDataList, { type DataColumn } from '../../components/common/dashboard/ResponsiveDataList'
import SectionHeader from '../../components/common/dashboard/SectionHeader'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import '../../styles/dashboard.css'
import '../../styles/school-admin.css'

type Filter = 'all' | 'assigned' | 'unassigned' | 'assessed' | 'pending' | 'pending_link'

export default function SchoolStudentsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<Filter>('all')
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([])
  const [bulkCounselorId, setBulkCounselorId] = useState('')
  const { downloadReport, downloadingId } = useDownloadReport()

  const studentsQ = useQuery({
    queryKey: ['school-admin', 'students'],
    queryFn: () => schoolAdminApi.getStudents().then(r => r.data.data),
  })
  const counselorsQ = useQuery({
    queryKey: ['school-admin', 'counselors'],
    queryFn: () => schoolAdminApi.getCounselors().then(r => r.data.data),
  })
  const membershipRequestsQ = useQuery({
    queryKey: ['school-admin', 'membership-requests'],
    queryFn: () => schoolAdminApi.getMembershipRequests().then(r => r.data.data),
  })

  const invalidateAssignmentData = () => {
    queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
    queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
    queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
  }

  const assignMutation = useMutation({
    mutationFn: ({ studentId, counselorId }: { studentId: number; counselorId: number }) =>
      schoolAdminApi.assignStudent(studentId, counselorId),
    onSuccess: (res) => {
      invalidateAssignmentData()
      toast.success(res.data.message)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to assign student.')
    },
  })

  const bulkAssignMutation = useMutation({
    mutationFn: () => schoolAdminApi.bulkAssignStudents(
      selectedStudentIds,
      Number(bulkCounselorId),
    ),
    onSuccess: (res) => {
      invalidateAssignmentData()
      toast.success(res.data.message)
      setSelectedStudentIds([])
      setBulkCounselorId('')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Could not assign the selected learners.')
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
      invalidateAssignmentData()
      toast.success(res.data.message)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Could not decide this school-link request.')
    },
  })

  const verificationMutation = useMutation({
    mutationFn: ({
      studentId,
      gradeId,
      verified,
    }: {
      studentId: number
      gradeId: number
      verified: boolean
    }) => schoolAdminApi.setGradeVerification(studentId, gradeId, verified),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      toast.success(response.data.message)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Could not update grade verification.')
    },
  })

  if (studentsQ.isLoading || counselorsQ.isLoading) {
    return <p className="loading-text">Loading learners…</p>
  }
  if (studentsQ.isError || counselorsQ.isError) {
    return (
      <ErrorState
        title="The learner list could not load"
        description="Learner and counsellor assignments are unchanged. Check your connection and try again."
        onRetry={() => {
          studentsQ.refetch()
          counselorsQ.refetch()
        }}
        actionLabel="Retry learners"
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  const counselors = counselorsQ.data ?? []
  const normalizedSearch = search.trim().toLowerCase()
  const filtered = (studentsQ.data ?? []).filter(student => {
    const matchesSearch = (
      !normalizedSearch
      || `${student.first_name} ${student.last_name}`.toLowerCase().includes(normalizedSearch)
      || student.email.toLowerCase().includes(normalizedSearch)
    )
    if (!matchesSearch) return false
    if (filter === 'assigned') return student.counselor_id !== null
    if (filter === 'unassigned') return (
      student.school_membership_status === 'active'
      && student.counselor_id === null
    )
    if (filter === 'assessed') return student.quiz_status === 'done'
    if (filter === 'pending') return student.quiz_status === 'pending'
    if (filter === 'pending_link') return student.school_membership_status === 'pending'
    return true
  })

  function toggleSelected(studentId: number) {
    setSelectedStudentIds(current => (
      current.includes(studentId)
        ? current.filter(id => id !== studentId)
        : [...current, studentId]
    ))
  }

  const columns: DataColumn<SchoolStudent>[] = [
    {
      key: 'learner',
      label: 'Learner',
      render: student => {
        const name = `${student.first_name} ${student.last_name}`
        const canBulkAssign = (
          student.school_membership_status === 'active'
          && student.counselor_id === null
        )
        return (
          <div className="admin-learner">
            {canBulkAssign && (
              <input
                type="checkbox"
                aria-label={`Select ${name}`}
                checked={selectedStudentIds.includes(student.id)}
                onChange={() => toggleSelected(student.id)}
              />
            )}
            <div className="admin-person">
              <strong>{name}</strong>
              <span>{student.email}</span>
              {student.transfer?.previous_membership_count > 0 && (
                <span>
                  Transferred in · {student.transfer.previous_membership_count} previous membership
                  {student.transfer.previous_membership_count === 1 ? '' : 's'}
                </span>
              )}
              {student.academic_evidence?.map(evidence => (
                <div className="admin-evidence" key={evidence.id}>
                  <span>
                    {evidence.subject_name} · Term {evidence.term} {evidence.year} · {evidence.level}
                  </span>
                  <small>{evidence.framework.code} {evidence.framework.version}</small>
                  <small>
                    {evidence.verified_school
                      ? `Verified by ${evidence.verified_school.name}`
                      : 'Learner-entered evidence'}
                  </small>
                  {evidence.can_verify && (
                    <button
                      type="button"
                      className="btn-ghost"
                      aria-label={`Verify ${evidence.subject_name} Term ${evidence.term}`}
                      disabled={verificationMutation.isPending}
                      onClick={() => verificationMutation.mutate({
                        studentId: student.id,
                        gradeId: evidence.id,
                        verified: true,
                      })}
                    >
                      {verificationMutation.isPending ? 'Saving…' : 'Verify'}
                    </button>
                  )}
                  {evidence.can_remove_verification && (
                    <button
                      type="button"
                      className="btn-ghost"
                      aria-label={`Remove verification for ${evidence.subject_name} Term ${evidence.term}`}
                      disabled={verificationMutation.isPending}
                      onClick={() => verificationMutation.mutate({
                        studentId: student.id,
                        gradeId: evidence.id,
                        verified: false,
                      })}
                    >
                      Remove verification
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      },
    },
    {
      key: 'status',
      label: 'Status',
      render: student => (
        <div className="admin-status-stack">
          <span className={`status-badge status-badge--${student.school_membership_status === 'active' ? 'assessed' : 'pending'}`}>
            {student.school_membership_status === 'active'
              ? 'School approved'
              : student.school_membership_status === 'pending'
                ? 'Link pending'
                : 'Link rejected'}
          </span>
          <span>
            Grade {student.grade} · {student.quiz_status === 'done' ? 'Assessed' : 'Assessment pending'}
          </span>
        </div>
      ),
    },
    {
      key: 'assignment',
      label: 'Assignment',
      render: student => (
        <div className="admin-assignment">
          <strong>{student.counselor_name ?? 'Unassigned'}</strong>
          <select
            className="assignment-select"
            aria-label={`Assign counsellor for ${student.first_name} ${student.last_name}`}
            value={student.counselor_id ?? ''}
            onChange={(event) => {
              if (event.target.value) {
                assignMutation.mutate({
                  studentId: student.id,
                  counselorId: Number(event.target.value),
                })
              }
            }}
            disabled={assignMutation.isPending || student.school_membership_status !== 'active'}
          >
            <option value="">Choose counsellor</option>
            {counselors.map(counselor => (
              <option key={counselor.id} value={counselor.id}>
                {counselor.first_name} {counselor.last_name} · {counselor.student_count}
              </option>
            ))}
          </select>
        </div>
      ),
    },
    {
      key: 'report',
      label: 'Report',
      align: 'end',
      render: student => (
        <button
          type="button"
          className="btn-ghost"
          onClick={() => downloadReport(student.id)}
          disabled={downloadingId === student.id || student.school_membership_status !== 'active'}
          aria-label={`Download report for ${student.first_name} ${student.last_name}`}
        >
          {downloadingId === student.id ? 'Generating…' : 'Download PDF'}
        </button>
      ),
    },
  ]

  const filters: { value: Filter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'assigned', label: 'Assigned' },
    { value: 'unassigned', label: 'Unassigned' },
    { value: 'assessed', label: 'Assessed' },
    { value: 'pending', label: 'Pending Assessment' },
    { value: 'pending_link', label: 'Pending School Link' },
  ]

  return (
    <div className="school-students-page">
      <SectionHeader
        titleAs="h1"
        eyebrow="School cohort"
        title="Learners"
        description="Approve school-link requests, assign counsellors, and track each learner's progress."
        className="school-students-page__header"
      />

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
            <button type="button" className="btn-ghost" onClick={() => membershipRequestsQ.refetch()}>
              Retry requests
            </button>
          </div>
        ) : membershipRequestsQ.data?.length ? (
          <div className="membership-queue__list">
            {membershipRequestsQ.data.map(request => {
              const name = `${request.first_name} ${request.last_name}`
              const deciding = (
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
                      {deciding ? 'Saving…' : 'Approve'}
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
          <p className="membership-queue__empty">No school-link requests are waiting for review.</p>
        )}
      </section>

      <div className="school-students-toolbar">
        <ManagementToolbar
          resultCount={`${filtered.length} learner${filtered.length === 1 ? '' : 's'}`}
          search={(
            <label htmlFor="student-search">
              <span>Search learners</span>
              <input
                id="student-search"
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name or email"
              />
            </label>
          )}
          filters={(
            <div className="admin-filter-chips" aria-label="Filter learners">
              {filters.map(item => (
                <button
                  type="button"
                  key={item.value}
                  className={filter === item.value ? 'btn-primary' : 'btn-ghost'}
                  onClick={() => setFilter(item.value)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        />
      </div>

      {selectedStudentIds.length > 0 && (
        <div className="bulk-assignment" aria-label="Bulk assignment">
          <strong>{selectedStudentIds.length} selected</strong>
          <label>
            <span>Counsellor for selected learners</span>
            <select
              value={bulkCounselorId}
              onChange={(event) => setBulkCounselorId(event.target.value)}
            >
              <option value="">Choose counsellor</option>
              {counselors.map(counselor => (
                <option key={counselor.id} value={counselor.id}>
                  {counselor.first_name} {counselor.last_name} · {counselor.student_count} learners
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn-primary"
            disabled={!bulkCounselorId || bulkAssignMutation.isPending}
            onClick={() => bulkAssignMutation.mutate()}
          >
            {bulkAssignMutation.isPending
              ? 'Assigning…'
              : `Assign ${selectedStudentIds.length} learner${selectedStudentIds.length === 1 ? '' : 's'}`}
          </button>
        </div>
      )}

      <ResponsiveDataList
        ariaLabel="Approved school learners"
        items={filtered}
        columns={columns}
        getKey={student => student.id}
        empty={<EmptyState title="No matching learners" description="Try a different search or cohort filter." />}
      />
    </div>
  )
}
