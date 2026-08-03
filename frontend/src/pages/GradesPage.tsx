import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi, StudentSubject } from '../api/students'
import SubjectList from '../components/students/SubjectList'
import GradeEntryForm from '../components/students/GradeEntryForm'
import GradeHistory from '../components/students/GradeHistory'
import AcademicProgressDashboard from '../components/students/AcademicProgressDashboard'
import ErrorState from '../components/common/dashboard/ErrorState'
import { isFeatureEnabled } from '../lib/featureFlags'
import '../styles/student-pages.css'

function LegacyGradesPage() {
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

  if (profileQ.isError || subjectsQ.isError || catalogQ.isError) {
    return (
      <ErrorState
        title="Your subjects and grades could not load"
        description="Your saved grades are unchanged. Check your connection and try loading them again."
        onRetry={() => {
          profileQ.refetch()
          subjectsQ.refetch()
          if (profileQ.data) catalogQ.refetch()
        }}
        actionLabel="Retry grade data"
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  const enrolled = subjectsQ.data ?? []
  const catalog = catalogQ.data ?? []
  const enrolledIds = new Set(enrolled.map((ss: StudentSubject) => ss.subject.id))
  const unenrolled = catalog.filter((subject) => !enrolledIds.has(subject.id))
  const activeSubject = enrolled.find((subject: StudentSubject) => subject.id === activeSubjectId)

  return (
    <div className="student-page student-page--grades">
      <header className="student-page__hero">
        <div>
          <span className="student-page__eyebrow">Your learning record</span>
          <h1>My subjects &amp; grades</h1>
          <p>Build a clear picture of how you are growing, one subject and one term at a time.</p>
        </div>
        <div className="student-page__hero-stat" aria-label={`${enrolled.length} subjects enrolled`}>
          <strong>{enrolled.length}</strong>
          <span>subjects enrolled</span>
        </div>
      </header>

      <div className="student-page__grid student-page__grid--grades">
        <div className="student-page__column">
          <section className="student-panel student-panel--tinted">
            <div className="student-panel__heading">
              <div>
                <span className="student-panel__kicker">Your collection</span>
                <h2>Enrolled subjects</h2>
              </div>
              <span className="student-panel__count">{enrolled.length}</span>
            </div>
            {subjectsQ.isLoading ? <p>Loading…</p> : (
              <SubjectList
                enrolledSubjects={enrolled}
                onRemove={(subject) => removeMutation.mutate(subject.id)}
                disabled={removeMutation.isPending}
              />
            )}
          </section>

          {unenrolled.length > 0 && (
            <section className="student-panel student-panel--compact">
              <div className="student-panel__heading">
                <div>
                  <span className="student-panel__kicker">Explore</span>
                  <h2>Add a subject</h2>
                </div>
              </div>
              <div className="subject-picker">
                {unenrolled.map((subject) => (
                  <button
                    key={subject.id}
                    type="button"
                    onClick={() => enrollMutation.mutate(subject.id)}
                    disabled={enrollMutation.isPending}
                    className="subject-picker__button"
                  >
                    <span aria-hidden="true">+</span> {subject.name}
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>

        {enrolled.length > 0 && (
          <section className="student-panel student-panel--workspace">
            <div className="student-panel__heading">
              <div>
                <span className="student-panel__kicker">Term tracker</span>
                <h2>{activeSubject ? activeSubject.subject.name : 'Enter grades'}</h2>
              </div>
              <span className="student-panel__mark" aria-hidden="true">↗</span>
            </div>

            <div className="subject-tabs" aria-label="Choose a subject">
              {enrolled.map((subject: StudentSubject) => (
                <button
                  key={subject.id}
                  type="button"
                  onClick={() => setActiveSubjectId(subject.id)}
                  className={`subject-tabs__button${activeSubjectId === subject.id ? ' is-active' : ''}`}
                >
                  {subject.subject.name}
                </button>
              ))}
            </div>

            {activeSubjectId === null ? (
              <div className="student-empty-state">
                <span className="student-empty-state__icon" aria-hidden="true">◎</span>
                <strong>Choose a subject</strong>
                <p>Select one above to add a term result and review its history.</p>
              </div>
            ) : (
              <>
                <GradeEntryForm studentSubjectId={activeSubjectId} />
                <div className="grade-history-wrap">
                  <h3>Grade history</h3>
                  {gradesQ.isLoading ? (
                    <p>Loading grades…</p>
                  ) : gradesQ.isError ? (
                    <ErrorState
                      title="Grade history could not load"
                      description="Try loading this subject's grade history again."
                      onRetry={() => gradesQ.refetch()}
                      actionLabel="Retry grade history"
                    />
                  ) : (
                    <GradeHistory grades={gradesQ.data ?? []} />
                  )}
                </div>
              </>
            )}
          </section>
        )}
      </div>
    </div>
  )
}

export default function GradesPage() {
  return isFeatureEnabled('academic_progress_v1')
    ? <AcademicProgressDashboard />
    : <LegacyGradesPage />
}
