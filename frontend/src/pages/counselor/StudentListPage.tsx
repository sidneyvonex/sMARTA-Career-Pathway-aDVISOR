import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { counselorApi } from '../../api/counselor'
import StudentFilterBar from '../../components/counselor/StudentFilterBar'
import StudentTable from '../../components/counselor/StudentTable'
import '../../styles/counselor.css'

function isNewStudent(lastActive: string | null): boolean {
  if (!lastActive) return false
  const fourteenDaysAgo = Date.now() - 14 * 24 * 60 * 60 * 1000
  return new Date(lastActive).getTime() >= fourteenDaysAgo
}

export default function StudentListPage() {
  const [activeFilter, setActiveFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['counselor-students'],
    queryFn: async () => {
      const res = await counselorApi.getStudents()
      return res.data.data
    },
  })

  useEffect(() => {
    if (isError) {
      toast.error("Couldn't load students. Please try again.")
    }
  }, [isError])

  const students = data ?? []

  const filtered = useMemo(() => {
    let list = students

    // Filter by status
    if (activeFilter === 'needs_attention') {
      list = list.filter((s) => s.quiz_status === 'pending')
    } else if (activeFilter === 'assessed') {
      list = list.filter((s) => s.quiz_status === 'done')
    } else if (activeFilter === 'new') {
      list = list.filter((s) => isNewStudent(s.last_active))
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      list = list.filter(
        (s) =>
          s.first_name.toLowerCase().includes(q) ||
          s.last_name.toLowerCase().includes(q)
      )
    }

    return list
  }, [students, activeFilter, searchQuery])

  return (
    <div className="counselor-page">
      <div className="counselor-page__header">
        <h1 className="counselor-page__title">My Students</h1>
        {!isLoading && (
          <span className="counselor-page__count">
            {students.length} student{students.length !== 1 ? 's' : ''} assigned
          </span>
        )}
      </div>

      <StudentFilterBar
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {isLoading ? (
        <div className="student-table-wrap">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton-row">
              <div className="skeleton skeleton-circle" />
              <div className="skeleton skeleton-bar skeleton-bar--long" />
              <div className="skeleton skeleton-bar skeleton-bar--short" />
              <div className="skeleton skeleton-bar skeleton-bar--medium" />
            </div>
          ))}
        </div>
      ) : (
        <StudentTable students={filtered} />
      )}
    </div>
  )
}
