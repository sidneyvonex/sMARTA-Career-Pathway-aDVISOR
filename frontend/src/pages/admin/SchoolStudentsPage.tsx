import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi, SchoolStudent } from '../../api/schoolAdmin'
import '../../styles/school-admin.css'

type Filter = 'all' | 'assigned' | 'unassigned' | 'assessed' | 'pending'

export default function SchoolStudentsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<Filter>('all')

  const { data: students, isLoading } = useQuery({
    queryKey: ['school-admin', 'students'],
    queryFn: () => schoolAdminApi.getStudents().then(r => r.data.data),
  })

  const { data: counselors } = useQuery({
    queryKey: ['school-admin', 'counselors'],
    queryFn: () => schoolAdminApi.getCounselors().then(r => r.data.data),
  })

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

  if (isLoading) return <p className="loading-text">Loading students…</p>

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
                    disabled={assignMutation.isPending}
                  >
                    <option value="">Unassigned</option>
                    {counselors?.map(c => (
                      <option key={c.id} value={c.id}>
                        {c.first_name} {c.last_name}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
