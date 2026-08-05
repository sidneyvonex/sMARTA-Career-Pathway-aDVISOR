import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  schoolAdminApi,
  type MarksImportResult,
  type SchoolStudent,
  type StudentImportResult,
} from '../../api/schoolAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ErrorState from '../../components/common/dashboard/ErrorState'
import ResponsiveDataList, { type DataColumn } from '../../components/common/dashboard/ResponsiveDataList'
import SectionHeader from '../../components/common/dashboard/SectionHeader'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import '../../styles/dashboard.css'
import '../../styles/school-admin.css'

type Filter = 'all' | 'assigned' | 'unassigned' | 'assessed' | 'pending' | 'pending_link'

function membershipStatus(student: SchoolStudent) {
  return student.membership?.status ?? student.school_membership_status
}

function downloadCsv(filename: string, rows: string[][]) {
  const escapeCell = (value: string) => {
    const protectedValue = /^[=+\-@]/.test(value) ? `'${value}` : value
    return `"${protectedValue.replace(/"/g, '""')}"`
  }
  const csv = rows.map(row => row.map(escapeCell).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default function SchoolStudentsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<Filter>('all')
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([])
  const [bulkCounselorId, setBulkCounselorId] = useState('')
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<StudentImportResult | null>(null)
  const importInputRef = useRef<HTMLInputElement>(null)
  const [marksFile, setMarksFile] = useState<File | null>(null)
  const [marksPeriodId, setMarksPeriodId] = useState('')
  const [marksPreview, setMarksPreview] = useState<MarksImportResult | null>(null)
  const marksInputRef = useRef<HTMLInputElement>(null)
  const { downloadStudentReport, downloadingId } = useDownloadReport()

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
  const periodsQ = useQuery({
    queryKey: ['school-admin', 'academic-periods'],
    queryFn: () => schoolAdminApi.getAcademicPeriods().then(r => r.data.data),
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

  const importMutation = useMutation({
    mutationFn: (file: File) => schoolAdminApi.importStudents(file),
    onSuccess: (response) => {
      const result = response.data.data
      setImportResult(result)
      setImportFile(null)
      if (importInputRef.current) importInputRef.current.value = ''
      invalidateAssignmentData()
      if (result.created_count + result.linked_count > 0) toast.success(response.data.message)
      else toast.error('No learner accounts were created. Review the row errors.')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'The learner CSV could not be imported.')
    },
  })

  const marksMutation = useMutation({
    mutationFn: ({ preview }: { preview: boolean }) => (
      schoolAdminApi.importMarks(Number(marksPeriodId), marksFile!, preview)
    ),
    onSuccess: (response, variables) => {
      if (variables.preview) {
        setMarksPreview(response.data.data)
        toast.success('Marks file checked. Review it before importing.')
        return
      }
      setMarksPreview(response.data.data)
      setMarksFile(null)
      if (marksInputRef.current) marksInputRef.current.value = ''
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      toast.success(response.data.message)
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(
        typeof message === 'string'
          ? message
          : 'The marks file could not be processed. Preview it and review the row errors.',
      )
    },
  })

  function downloadCredentials() {
    if (!importResult?.created.length) return
    downloadCsv('learner-login-credentials.csv', [
      ['first_name', 'last_name', 'email', 'grade', 'temporary_password'],
      ...importResult.created.map(learner => [
        learner.first_name,
        learner.last_name,
        learner.email,
        String(learner.grade),
        learner.temporary_password,
      ]),
    ])
  }

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
      membershipStatus(student) === 'active'
      && student.counselor_id === null
    )
    if (filter === 'assessed') return student.quiz_status === 'done'
    if (filter === 'pending') return student.quiz_status === 'pending'
    if (filter === 'pending_link') return membershipStatus(student) === 'pending'
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
          membershipStatus(student) === 'active'
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
              {student.academic_evidence?.map(evidence => {
                const canVerify = (
                  evidence.can_verify
                  && (
                    evidence.verified_school === null
                    || evidence.verified_school.id === student.school?.id
                  )
                )
                return (
                  <div className="admin-evidence" key={evidence.id}>
                    <span>
                      {evidence.subject_name} · Term {evidence.term} {evidence.year} · {evidence.level}
                    </span>
                    <small>{evidence.framework.code} {evidence.framework.version}</small>
                    <small>
                      {evidence.verified_school && evidence.verified_at
                        ? `Verified by ${evidence.verified_school.name}`
                        : evidence.verified_school
                          ? `Previously verified by ${evidence.verified_school.name}; verification removed`
                          : `${evidence.source === 'school' ? 'School' : 'Learner'}-entered evidence`}
                    </small>
                    {canVerify && (
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
                )
              })}
            </div>
          </div>
        )
      },
    },
    {
      key: 'status',
      label: 'Status',
      render: student => {
        const status = membershipStatus(student)
        return (
          <div className="admin-status-stack">
            <span className={`status-badge status-badge--${status === 'active' ? 'assessed' : 'pending'}`}>
              {status === 'active'
                ? 'School approved'
                : status === 'pending'
                  ? 'Link pending'
                  : 'Link rejected'}
            </span>
            <span>
              Grade {student.grade} · {student.quiz_status === 'done' ? 'Assessed' : 'Assessment pending'}
            </span>
          </div>
        )
      },
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
            disabled={assignMutation.isPending || membershipStatus(student) !== 'active'}
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
          onClick={() => downloadStudentReport(student.id)}
          disabled={downloadingId === student.id || membershipStatus(student) !== 'active'}
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

      <section className="marks-import" aria-labelledby="marks-import-title">
        <div className="marks-import__copy">
          <p className="membership-queue__eyebrow">Completed-term evidence</p>
          <h2 id="marks-import-title">Upload school marks</h2>
          <p>
            Choose a completed term, preview every row, then import the official results.
            Unfinished and closed terms cannot receive marks.
          </p>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => downloadCsv('school-marks-template.csv', [
              ['student_email', 'subject_code', 'level', 'raw_score'],
              ['learner@example.com', 'MAT9', 'ME1', '72.5'],
            ])}
          >
            Download marks template
          </button>
        </div>
        <form
          className="marks-import__form"
          onSubmit={(event) => {
            event.preventDefault()
            if (marksFile && marksPeriodId) marksMutation.mutate({ preview: true })
          }}
        >
          <label htmlFor="marks-period">Academic period</label>
          <select
            id="marks-period"
            value={marksPeriodId}
            onChange={(event) => {
              setMarksPeriodId(event.target.value)
              setMarksPreview(null)
            }}
            disabled={periodsQ.isLoading || periodsQ.isError}
          >
            <option value="">Choose a completed term</option>
            {(periodsQ.data ?? []).map(period => (
              <option key={period.id} value={period.id} disabled={!period.can_submit}>
                Term {period.term} {period.year} ({period.state.replace('_', ' ')})
              </option>
            ))}
          </select>
          {periodsQ.isError && (
            <small role="alert">Academic periods could not load. Refresh before uploading marks.</small>
          )}
          {!periodsQ.isLoading && !periodsQ.isError && !(periodsQ.data ?? []).some(period => period.can_submit) && (
            <small>No completed term currently has an open marks window.</small>
          )}
          <label htmlFor="marks-import-file">Marks CSV file</label>
          <input
            ref={marksInputRef}
            id="marks-import-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setMarksFile(event.target.files?.[0] ?? null)
              setMarksPreview(null)
            }}
          />
          <small>Required: student_email, subject_code, level. raw_score is optional.</small>
          <button
            type="submit"
            className="btn-primary"
            disabled={!marksFile || !marksPeriodId || marksMutation.isPending}
          >
            {marksMutation.isPending && marksMutation.variables?.preview
              ? 'Checking marksâ€¦'
              : 'Preview marks'}
          </button>
        </form>
        {marksPreview && (
          <div
            className={`marks-import__result ${marksPreview.error_count ? 'marks-import__result--error' : ''}`}
            role="status"
          >
            <div>
              <strong>{marksPreview.valid_count} valid row{marksPreview.valid_count === 1 ? '' : 's'}</strong>
              <span>{marksPreview.error_count} error{marksPreview.error_count === 1 ? '' : 's'}</span>
            </div>
            {marksPreview.error_count > 0 ? (
              <details open>
                <summary>Rows that need attention</summary>
                <ul>
                  {marksPreview.rows.filter(row => row.errors.length > 0).map(row => (
                    <li key={row.row}>Row {row.row}: {row.errors.join('; ')}</li>
                  ))}
                </ul>
              </details>
            ) : marksPreview.created_count !== undefined ? (
              <p>
                {marksPreview.created_count} result{marksPreview.created_count === 1 ? '' : 's'} created
                {' Â· '}{marksPreview.replaced_count ?? 0} learner entr{marksPreview.replaced_count === 1 ? 'y' : 'ies'} replaced
              </p>
            ) : (
              <button
                type="button"
                className="btn-primary"
                disabled={marksMutation.isPending}
                onClick={() => marksMutation.mutate({ preview: false })}
              >
                {marksMutation.isPending ? 'Importing marksâ€¦' : 'Import and verify marks'}
              </button>
            )}
          </div>
        )}
      </section>

      <section className="student-import" aria-labelledby="student-import-title">
        <div className="student-import__copy">
          <p className="membership-queue__eyebrow">Bulk enrolment</p>
          <h2 id="student-import-title">Import learners from CSV</h2>
          <p>
            Add up to 500 learners at once. Each account receives a temporary password
            that is shown only after this import.
          </p>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => downloadCsv('learner-import-template.csv', [
              ['first_name', 'last_name', 'email', 'grade'],
              ['Amina', 'Kamau', 'amina@example.com', '9'],
            ])}
          >
            Download CSV template
          </button>
        </div>
        <form
          className="student-import__form"
          onSubmit={(event) => {
            event.preventDefault()
            if (importFile) importMutation.mutate(importFile)
          }}
        >
          <label htmlFor="student-import-file">Learner CSV file</label>
          <input
            ref={importInputRef}
            id="student-import-file"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setImportFile(event.target.files?.[0] ?? null)
              setImportResult(null)
            }}
          />
          <small>Required columns: first_name, last_name, email, grade.</small>
          <button
            type="submit"
            className="btn-primary"
            disabled={!importFile || importMutation.isPending}
          >
            {importMutation.isPending ? 'Importing learners…' : 'Import learners'}
          </button>
        </form>
        {importResult && (
          <div className="student-import__result" role="status">
            <div>
              <strong>
                {importResult.created_count + importResult.linked_count} learner
                {importResult.created_count + importResult.linked_count === 1 ? '' : 's'} added
              </strong>
              <span>{importResult.error_count} row{importResult.error_count === 1 ? '' : 's'} skipped</span>
            </div>
            <p>
              {importResult.created_count} new account{importResult.created_count === 1 ? '' : 's'} created
              {' · '}{importResult.linked_count} existing account{importResult.linked_count === 1 ? '' : 's'} linked
              {importResult.already_linked_count > 0
                ? ` · ${importResult.already_linked_count} already in this cohort`
                : ''}
            </p>
            {importResult.linked_count > 0 && (
              <p>
                Existing learners keep their current password. They can use “Forgot password”
                on the login page if they no longer know it.
              </p>
            )}
            {importResult.created_count > 0 && (
              <>
                <p>
                  Download these passwords now and store them securely. They cannot be shown again.
                </p>
                <button type="button" className="btn-primary" onClick={downloadCredentials}>
                  Download login credentials
                </button>
              </>
            )}
            {importResult.errors.length > 0 && (
              <details>
                <summary>Review skipped rows</summary>
                <ul>
                  {importResult.errors.map(error => (
                    <li key={`${error.row}-${error.email}`}>
                      Row {error.row}{error.email ? ` (${error.email})` : ''}: {error.message}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}
      </section>

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
