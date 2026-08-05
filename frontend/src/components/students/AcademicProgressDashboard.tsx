import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import toast from 'react-hot-toast'

import {
  studentsApi,
  type AcademicGrade,
  type ProgressEvidence,
  type StudentSubject,
  type Subject,
} from '../../api/students'
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
import SubjectList from './SubjectList'
import AcademicProgressExplorer from './AcademicProgressExplorer'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import { useAuthStore } from '../../store/authStore'


type FilterValue = 'all' | string


function actionErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ message?: unknown }>
  if (!axiosError.response) return 'Connection error. Please check your internet.'
  const status = axiosError.response.status
  if (status === 403) return "You don't have permission to do that."
  if (status === 404) return 'That item no longer exists.'
  if (status >= 500) return 'Server error. Please try again in a moment.'
  const message = axiosError.response.data?.message
  return typeof message === 'string' && message.trim()
    ? message
    : 'Something went wrong. Please try again.'
}


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
  const queryClient = useQueryClient()
  const { downloadStudentReport, downloadingId } = useDownloadReport()
  const authenticatedStudentId = useAuthStore((state) => state.user?.id)
  const [academicGrade, setAcademicGrade] = useState<FilterValue>('all')
  const [year, setYear] = useState<FilterValue>('all')
  const [recordOpen, setRecordOpen] = useState(false)
  const [activeSubjectId, setActiveSubjectId] = useState<number | null>(null)
  const recordPanelRef = useRef<HTMLElement>(null)
  const recordHeadingRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    if (!recordOpen) return
    recordPanelRef.current?.scrollIntoView?.({ block: 'start' })
    recordHeadingRef.current?.focus()
  }, [recordOpen])

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
  const profileQ = useQuery({
    queryKey: ['student-profile'],
    queryFn: () => studentsApi.getProfile().then((response) => response.data.data),
  })
  const catalogQ = useQuery({
    queryKey: ['subjects-catalog', profileQ.data?.grade],
    queryFn: () => studentsApi.getSubjects(profileQ.data!.grade).then((response) => response.data.data),
    enabled: profileQ.data !== undefined,
  })
  const gradesQ = useQuery({
    queryKey: ['grades', activeSubjectId],
    queryFn: () => studentsApi.getGrades(activeSubjectId!).then((response) => response.data.data),
    enabled: activeSubjectId !== null,
  })
  const refreshAcademicEvidence = () => {
    queryClient.invalidateQueries({ queryKey: ['my-subjects'] })
    queryClient.invalidateQueries({ queryKey: ['students', 'academic-progress'] })
    queryClient.invalidateQueries({ queryKey: academicGoalKeys.all })
  }
  const enroll = useMutation({
    mutationFn: (subject: Subject) => studentsApi.enrollSubject(subject.id)
      .then((response) => ({ response, subject })),
    onSuccess: ({ response, subject }) => {
      toast.success(`${subject.name} added to your subjects.`)
      setActiveSubjectId(response.data.data.id)
      refreshAcademicEvidence()
    },
    onError: (error) => toast.error(actionErrorMessage(error)),
  })
  const archive = useMutation({
    mutationFn: (subject: StudentSubject) => studentsApi.removeSubject(subject.id)
      .then((response) => ({ response, subject })),
    onSuccess: ({ subject }) => {
      toast.success(`${subject.subject.name} removed.`)
      if (activeSubjectId === subject.id) setActiveSubjectId(null)
      refreshAcademicEvidence()
    },
    onError: (error) => toast.error(actionErrorMessage(error)),
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

  if (
    progressQ.isError || goalsQ.isError || educationGoalsQ.isError ||
    subjectsQ.isError || profileQ.isError || catalogQ.isError
  ) {
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
          profileQ.refetch()
          if (profileQ.data) catalogQ.refetch()
        }}
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  if (!progress) return null

  const subjects = subjectsQ.data ?? []
  const enrolledSubjectIds = new Set(subjects.map((item) => item.subject.id))
  const availableSubjects = (catalogQ.data ?? []).filter(
    (subject) => !enrolledSubjectIds.has(subject.id),
  )
  const openRecordPanel = (subjectId?: number) => {
    setActiveSubjectId((current) => subjectId ?? current ?? subjects[0]?.id ?? null)
    setRecordOpen(true)
  }
  const studentSubjectIdByContinuityCode = new Map(
    subjects.map((item) => [item.continuity_code, item.id]),
  )

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

      <section className="progress-panel progress-subject-management" aria-labelledby="manage-subjects-title">
        <div className="progress-section-heading">
          <div>
            <h2 id="manage-subjects-title">Manage subjects</h2>
            <p>Keep your active subjects current. Archiving preserves their recorded history.</p>
          </div>
        </div>
        {subjectsQ.isLoading || profileQ.isLoading || catalogQ.isLoading ? (
          <LoadingSkeleton label="Loading subject management" rows={2} variant="list" />
        ) : (
          <div className="progress-subject-management__grid">
            <div>
              <h3>Active subjects</h3>
              <SubjectList
                enrolledSubjects={subjects}
                onRemove={(subject) => archive.mutate(subject)}
                disabled={archive.isPending || enroll.isPending}
              />
            </div>
            <div>
              <h3>Add a subject</h3>
              {availableSubjects.length > 0 ? (
                <div className="subject-picker">
                  {availableSubjects.map((subject) => (
                    <button
                      key={subject.id}
                      type="button"
                      className="subject-picker__button"
                      onClick={() => enroll.mutate(subject)}
                      disabled={archive.isPending || enroll.isPending}
                      aria-label={`Add ${subject.name}`}
                    >
                      <span aria-hidden="true">+</span> {subject.name}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="progress-panel__empty">All current catalogue subjects are active.</p>
              )}
            </div>
          </div>
        )}
      </section>

      {progress.subjects.length === 0 ? (
        <>
          {subjectsQ.isLoading && (
            <LoadingSkeleton label="Loading enrolled subjects" rows={1} variant="list" />
          )}
          {!subjectsQ.isLoading && subjects.length === 0 && (
            <EmptyState
              title="Add a subject to get started"
              description="Add a subject above, then record your first term result to begin building an explainable subject progress view."
            />
          )}
          {!subjectsQ.isLoading && subjects.length > 0 && (
            <EmptyState
              title="Start your academic evidence"
              description="Record a term result to begin building an explainable subject progress view."
              action={{ label: 'Record your first result', onClick: () => openRecordPanel() }}
            />
          )}
        </>
      ) : (
        <>
          <AcademicProgressExplorer
            progress={progress}
            onDownload={authenticatedStudentId
              ? (filters) => downloadStudentReport(authenticatedStudentId, filters)
              : undefined}
            downloading={authenticatedStudentId !== undefined && downloadingId === authenticatedStudentId}
          />
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
                  onClick={() => openRecordPanel()}
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
                {visibleSubjects.map((item) => {
                  const subjectId = studentSubjectIdByContinuityCode.get(item.progress.continuity_code)
                  return (
                    <ProgressSubjectCard
                      key={item.progress.continuity_code}
                      progress={item.progress}
                      evidence={item.evidence}
                      onRecordResult={subjectId === undefined
                        ? undefined
                        : () => openRecordPanel(subjectId)}
                      recordResultDisabled={subjectsQ.isLoading}
                    />
                  )
                })}
              </div>
            )}
          </section>
        </>
      )}

      {recordOpen && (
        <section
          ref={recordPanelRef}
          className="progress-panel progress-record"
          aria-labelledby="record-evidence-title"
        >
          <div className="progress-section-heading">
            <div>
              <h2 id="record-evidence-title" ref={recordHeadingRef} tabIndex={-1}>Record academic evidence</h2>
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
                      <GradeHistory grades={gradesQ.data ?? []} studentSubjectId={activeSubjectId} />
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
