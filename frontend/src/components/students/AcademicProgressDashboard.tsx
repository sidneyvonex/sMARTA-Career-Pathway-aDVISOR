import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { studentsApi, type AcademicGrade, type ProgressEvidence } from '../../api/students'
import { tertiaryApi } from '../../api/tertiary'
import { academicGoalKeys } from '../../hooks/useAcademicGoalMutations'
import { educationGoalKeys } from '../../hooks/useEducationGoalMutations'
import EmptyState from '../common/dashboard/EmptyState'
import ErrorState from '../common/dashboard/ErrorState'
import LoadingSkeleton from '../common/dashboard/LoadingSkeleton'
import AcademicTargetPanel from './AcademicTargetPanel'
import EducationGoalPreview from './EducationGoalPreview'
import GradeEntryForm from './GradeEntryForm'
import GradeHistory from './GradeHistory'
import ProgressSubjectCard from './ProgressSubjectCard'


type FilterValue = 'all' | string


function matchesFilters(
  evidence: ProgressEvidence,
  academicGrade: FilterValue,
  year: FilterValue,
): boolean {
  const matchesGrade = academicGrade === 'all' || evidence.academic_grade === Number(academicGrade)
  const matchesYear = year === 'all' || evidence.year === Number(year)
  return matchesGrade && matchesYear
}


export default function AcademicProgressDashboard() {
  const [academicGrade, setAcademicGrade] = useState<FilterValue>('all')
  const [year, setYear] = useState<FilterValue>('all')
  const [recordOpen, setRecordOpen] = useState(false)
  const [activeSubjectId, setActiveSubjectId] = useState<number | null>(null)

  const progressQ = useQuery({
    queryKey: ['students', 'academic-progress'],
    queryFn: () => studentsApi.getProgress().then((response) => response.data.data),
  })
  const goalsQ = useQuery({
    queryKey: academicGoalKeys.all,
    queryFn: () => studentsApi.getAcademicGoals().then((response) => response.data.data),
  })
  const educationGoalsQ = useQuery({
    queryKey: educationGoalKeys.all,
    queryFn: () => tertiaryApi.getEducationGoals().then((response) => response.data.data),
  })
  const subjectsQ = useQuery({
    queryKey: ['my-subjects'],
    queryFn: () => studentsApi.getMySubjects().then((response) => response.data.data),
  })
  const gradesQ = useQuery({
    queryKey: ['grades', activeSubjectId],
    queryFn: () => studentsApi.getGrades(activeSubjectId!).then((response) => response.data.data),
    enabled: activeSubjectId !== null,
  })

  const progress = progressQ.data
  const years = useMemo(() => Array.from(new Set(
    (progress?.subjects ?? []).flatMap((item) => item.evidence.map((record) => record.year)),
  )).sort((a, b) => b - a), [progress])

  const visibleSubjects = useMemo(() => (progress?.subjects ?? []).flatMap((item) => {
    const evidence = item.evidence.filter((record) => matchesFilters(record, academicGrade, year))
    const hasActiveFilter = academicGrade !== 'all' || year !== 'all'
    return hasActiveFilter && evidence.length === 0 ? [] : [{ progress: item, evidence }]
  }), [academicGrade, progress, year])

  if (progressQ.isLoading) {
    return <LoadingSkeleton label="Loading academic progress" rows={6} variant="page" />
  }

  if (progressQ.isError || goalsQ.isError || educationGoalsQ.isError || subjectsQ.isError) {
    return (
      <ErrorState
        title="Academic progress could not load"
        description="Your evidence and goals are unchanged. Check your connection and try again."
        actionLabel="Retry progress"
        onRetry={() => {
          progressQ.refetch()
          goalsQ.refetch()
          educationGoalsQ.refetch()
          subjectsQ.refetch()
        }}
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  if (!progress) return null

  const subjects = subjectsQ.data ?? []
  const openRecordPanel = () => {
    setActiveSubjectId((current) => current ?? subjects[0]?.id ?? null)
    setRecordOpen(true)
  }

  return (
    <div className="student-page progress-page">
      <header className={`progress-hero progress-hero--${progress.overall.status}`}>
        <div className="progress-hero__copy">
          <h1>My progress</h1>
          <p>See the evidence behind each subject status, then choose one useful next step.</p>
        </div>
        <div className="progress-hero__summary" aria-label="Academic progress summary">
          <span>Current readiness</span>
          <strong>{progress.overall.label}</strong>
          <small>
            {progress.subjects.length} {progress.subjects.length === 1 ? 'subject' : 'subjects'} reviewed
          </small>
        </div>
      </header>

      {progress.subjects.length === 0 ? (
        <>
          <EmptyState
            title="Start your academic evidence"
            description="Record a term result to begin building an explainable subject progress view."
            action={subjectsQ.isLoading
              ? undefined
              : { label: 'Record your first result', onClick: openRecordPanel }}
          />
          {subjectsQ.isLoading && (
            <LoadingSkeleton label="Loading enrolled subjects" rows={1} variant="list" />
          )}
        </>
      ) : (
        <>
          <section className="progress-overview" aria-labelledby="subject-progress-title">
            <div className="progress-section-heading">
              <div>
                <h2 id="subject-progress-title">Subject progress</h2>
                <p>Statuses use all available evidence. Filters change the evidence shown below.</p>
              </div>
              <div className="progress-section-action">
                <button
                  type="button"
                  className="student-action student-action--secondary"
                  onClick={openRecordPanel}
                  disabled={subjectsQ.isLoading}
                >
                  Record a result
                </button>
                {subjectsQ.isLoading && (
                  <span role="status" aria-label="Loading enrolled subjects">Loading subjects…</span>
                )}
              </div>
            </div>

            <div className="progress-filters" aria-label="Filter academic evidence">
              <div className="student-field">
                <label htmlFor="progress-grade-filter">Academic grade</label>
                <select
                  id="progress-grade-filter"
                  className="student-field__control"
                  value={academicGrade}
                  onChange={(event) => setAcademicGrade(event.target.value)}
                >
                  <option value="all">All academic grades</option>
                  {([9, 10, 11, 12] satisfies AcademicGrade[]).map((grade) => (
                    <option key={grade} value={grade}>Grade {grade}</option>
                  ))}
                </select>
              </div>
              <div className="student-field">
                <label htmlFor="progress-year-filter">Academic year</label>
                <select
                  id="progress-year-filter"
                  className="student-field__control"
                  value={year}
                  onChange={(event) => setYear(event.target.value)}
                >
                  <option value="all">All academic years</option>
                  {years.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </div>
            </div>

            {visibleSubjects.length === 0 ? (
              <EmptyState
                title="No evidence matches these filters"
                description="Choose another academic grade or year to review your subject evidence."
                action={{
                  label: 'Clear filters',
                  onClick: () => {
                    setAcademicGrade('all')
                    setYear('all')
                  },
                }}
              />
            ) : (
              <div className="progress-subject-list">
                {visibleSubjects.map((item) => (
                  <ProgressSubjectCard
                    key={item.progress.continuity_code}
                    progress={item.progress}
                    evidence={item.evidence}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {recordOpen && (
        <section className="progress-panel progress-record" aria-labelledby="record-evidence-title">
          <div className="progress-section-heading">
            <div>
              <h2 id="record-evidence-title">Record academic evidence</h2>
              <p>Add a term result and review the subject history already saved.</p>
            </div>
            <button type="button" className="student-action student-action--secondary" onClick={() => setRecordOpen(false)}>
              Close
            </button>
          </div>
          {subjects.length === 0 ? (
            <p className="progress-panel__empty">Add an active subject before recording a result.</p>
          ) : (
            <>
              <div className="student-field progress-record__subject">
                <label htmlFor="evidence-subject">Record for subject</label>
                <select
                  id="evidence-subject"
                  className="student-field__control"
                  value={activeSubjectId ?? subjects[0].id}
                  onChange={(event) => setActiveSubjectId(Number(event.target.value))}
                >
                  {subjects.map((item) => (
                    <option key={item.id} value={item.id}>{item.subject.name}</option>
                  ))}
                </select>
              </div>
              {activeSubjectId !== null && (
                <>
                  <GradeEntryForm studentSubjectId={activeSubjectId} />
                  <div className="grade-history-wrap">
                    <h3>Grade history</h3>
                    {gradesQ.isLoading ? (
                      <LoadingSkeleton label="Loading grade history" rows={3} variant="list" />
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
            </>
          )}
        </section>
      )}

      <div className="progress-goal-grid">
        <AcademicTargetPanel
          goals={goalsQ.data ?? []}
          subjects={progress.subjects}
          isLoading={goalsQ.isLoading}
        />
        <EducationGoalPreview
          goals={educationGoalsQ.data ?? []}
          isLoading={educationGoalsQ.isLoading}
        />
      </div>

      <p className="progress-disclaimer">{progress.advisory_disclaimer}</p>
    </div>
  )
}
