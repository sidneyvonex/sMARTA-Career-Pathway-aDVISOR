import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { counselorApi } from '../../api/counselor'
import StudentFilterBar from '../../components/counselor/StudentFilterBar'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ErrorState from '../../components/common/dashboard/ErrorState'
import LoadingSkeleton from '../../components/common/dashboard/LoadingSkeleton'
import StatusBadge from '../../components/common/dashboard/StatusBadge'
import { formatCounty, initials, isNewStudent } from '../../lib/format'
import '../../styles/counselor.css'

export default function StudentListPage() {
  const [activeFilter, setActiveFilter] = useState('all')
  const [reasonFilter, setReasonFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const studentsQ = useQuery({
    queryKey: ['counselor', 'students'],
    queryFn: () => counselorApi.getStudents().then((response) => response.data.data),
  })

  useEffect(() => {
    if (studentsQ.isError) {
      toast.error("Couldn't load students. Please try again.")
    }
  }, [studentsQ.isError])

  const students = studentsQ.data ?? []
  const filtered = useMemo(() => {
    let list = students
    if (activeFilter === 'needs_attention') {
      list = list.filter((student) => student.needs_attention)
    } else if (activeFilter === 'assessed') {
      list = list.filter((student) => student.quiz_status === 'done')
    } else if (activeFilter === 'new') {
      list = list.filter((student) => isNewStudent(student.last_active))
    }
    if (reasonFilter !== 'all') {
      list = list.filter((student) => (
        student.attention_reasons.some((reason) => reason.code === reasonFilter)
      ))
    }
    const query = searchQuery.trim().toLowerCase()
    if (query) {
      list = list.filter((student) => (
        `${student.first_name} ${student.last_name}`.toLowerCase().includes(query)
      ))
    }
    return list
  }, [activeFilter, reasonFilter, searchQuery, students])

  return (
    <div className="counselor-page">
      <header className="counselor-page__header">
        <div>
          <span className="counselor-page__eyebrow">Assigned learners</span>
          <h1 className="counselor-page__title">My Students</h1>
        </div>
        {!studentsQ.isLoading && (
          <span className="counselor-page__count">
            {students.length} student{students.length === 1 ? '' : 's'} assigned
          </span>
        )}
      </header>

      <StudentFilterBar
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        reasonFilter={reasonFilter}
        onReasonChange={setReasonFilter}
      />

      {studentsQ.isLoading && (
        <LoadingSkeleton label="Loading assigned learners" rows={5} />
      )}
      {studentsQ.isError && (
        <ErrorState
          title="The learner caseload could not load"
          description="Check your connection and retry the assigned learner list."
          onRetry={() => studentsQ.refetch()}
        />
      )}
      {!studentsQ.isLoading && !studentsQ.isError && filtered.length === 0 && (
        <EmptyState
          title="No learners match these filters"
          description="Clear a status, attention reason or search term to see more learners."
          action={{
            label: 'Clear filters',
            onClick: () => {
              setActiveFilter('all')
              setReasonFilter('all')
              setSearchQuery('')
            },
          }}
        />
      )}
      {!studentsQ.isLoading && !studentsQ.isError && filtered.length > 0 && (
        <div className="counselor-caseload" aria-label="Assigned learner caseload">
          {filtered.map((student) => (
            <article className="counselor-caseload__card" key={student.id}>
              <div className="counselor-caseload__identity">
                <div aria-hidden="true">{initials(student.first_name, student.last_name)}</div>
                <div>
                  <h2>{student.first_name} {student.last_name}</h2>
                  <p>Grade {student.grade} · {formatCounty(student.county) ?? 'County not set'}</p>
                </div>
                <StatusBadge tone={student.needs_attention ? 'warning' : 'positive'}>
                  {student.needs_attention ? 'Needs attention' : 'Up to date'}
                </StatusBadge>
              </div>

              <div className="counselor-caseload__alignment">
                <span>Interest alignment</span>
                <strong>{student.top_pathway ?? 'Assessment not completed'}</strong>
              </div>

              <div className="counselor-caseload__reasons">
                {student.attention_reasons.length > 0 ? (
                  student.attention_reasons.map((reason) => (
                    <span key={reason.code}>{reason.label}</span>
                  ))
                ) : (
                  <span className="counselor-caseload__clear">No current attention reasons</span>
                )}
              </div>

              <Link to={`/counselor/students/${student.id}`}>
                Review learner
                <span aria-hidden="true">→</span>
              </Link>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
