import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi, StudentSubject } from '../api/students'
import SubjectList from '../components/students/SubjectList'
import GradeEntryForm from '../components/students/GradeEntryForm'
import GradeHistory from '../components/students/GradeHistory'

export default function GradesPage() {
  const qc = useQueryClient()
  const [activeSubjectId, setActiveSubjectId] = useState<number | null>(null)

  const profileQ = useQuery({
    queryKey: ['student-profile'],
    queryFn: () => studentsApi.getProfile().then((r) => r.data.data),
  })

  const subjectsQ = useQuery({
    queryKey: ['my-subjects'],
    queryFn: () => studentsApi.getMySubjects().then((r) => r.data.data),
  })

  const catalogQ = useQuery({
    queryKey: ['subjects-catalog', profileQ.data?.grade],
    queryFn: () => studentsApi.getSubjects(profileQ.data!.grade).then((r) => r.data.data),
    enabled: !!profileQ.data,
  })

  const gradesQ = useQuery({
    queryKey: ['grades', activeSubjectId],
    queryFn: () => studentsApi.getGrades(activeSubjectId!).then((r) => r.data.data),
    enabled: activeSubjectId !== null,
  })

  const enrollMutation = useMutation({
    mutationFn: (subjectId: number) => studentsApi.enrollSubject(subjectId),
    onSuccess: () => {
      toast.success('Subject added.')
      qc.invalidateQueries({ queryKey: ['my-subjects'] })
    },
    onError: () => toast.error('Could not add subject.'),
  })

  const removeMutation = useMutation({
    mutationFn: (id: number) => studentsApi.removeSubject(id),
    onSuccess: () => {
      toast.success('Subject removed.')
      qc.invalidateQueries({ queryKey: ['my-subjects'] })
      setActiveSubjectId(null)
    },
    onError: () => toast.error('Could not remove subject.'),
  })

  const enrolled = subjectsQ.data ?? []
  const catalog = catalogQ.data ?? []
  const enrolledIds = new Set(enrolled.map((ss: StudentSubject) => ss.subject.id))
  const unenrolled = catalog.filter((s) => !enrolledIds.has(s.id))

  return (
    <main style={{ maxWidth: '760px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontFamily: 'Inter, sans-serif', color: 'var(--color-text)', marginBottom: '1.5rem' }}>
        My Subjects & Grades
      </h1>

      <section style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Enrolled Subjects</h2>
        {subjectsQ.isLoading ? <p>Loading…</p> : (
          <SubjectList
            enrolledSubjects={enrolled}
            onRemove={(id) => removeMutation.mutate(id)}
          />
        )}
      </section>

      {unenrolled.length > 0 && (
        <section style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
          <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Add a Subject</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {unenrolled.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => enrollMutation.mutate(s.id)}
                disabled={enrollMutation.isPending}
                style={{ padding: '0.4rem 0.9rem', background: 'var(--color-background)', border: '1px solid var(--color-border)', borderRadius: '20px', cursor: 'pointer', fontSize: '0.875rem' }}
              >
                + {s.name}
              </button>
            ))}
          </div>
        </section>
      )}

      {enrolled.length > 0 && (
        <section style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
          <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Enter Grades</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            {enrolled.map((ss: StudentSubject) => (
              <button
                key={ss.id}
                type="button"
                onClick={() => setActiveSubjectId(ss.id)}
                style={{
                  padding: '0.4rem 0.9rem',
                  background: activeSubjectId === ss.id ? 'var(--color-primary)' : 'var(--color-background)',
                  color: activeSubjectId === ss.id ? '#fff' : 'var(--color-text)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '20px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                {ss.subject.name}
              </button>
            ))}
          </div>

          {activeSubjectId !== null && (
            <>
              <GradeEntryForm studentSubjectId={activeSubjectId} />
              <div style={{ marginTop: '1rem' }}>
                {gradesQ.isLoading ? <p>Loading grades…</p> : (
                  <GradeHistory grades={gradesQ.data ?? []} />
                )}
              </div>
            </>
          )}
        </section>
      )}
    </main>
  )
}
