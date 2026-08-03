import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { counselorApi, type CounselorNote } from '../../api/counselor'
import type { RIASECDimension } from '../../api/assessment'
import StudentDetailHeader from '../../components/counselor/StudentDetailHeader'
import CounselorGradesTable from '../../components/counselor/CounselorGradesTable'
import NoteCard from '../../components/counselor/NoteCard'
import NoteForm from '../../components/counselor/NoteForm'
import ScoreBars from '../../components/assessment/ScoreBars'
import RecommendationCards from '../../components/assessment/RecommendationCards'
import StatusBadge from '../../components/common/dashboard/StatusBadge'
import ResponsiveDataList from '../../components/common/dashboard/ResponsiveDataList'
import { GRADE_LEVEL_LABELS } from '../../api/students'
import { evidenceOrigin, evidenceVerification } from '../../lib/academicEvidence'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import '../../styles/counselor.css'


function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(value))
}


export default function StudentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const studentId = Number(id)
  const queryClient = useQueryClient()

  const { downloadReport, downloadingId } = useDownloadReport()
  const [editingNote, setEditingNote] = useState<CounselorNote | null>(null)
  const [category, setCategory] = useState<'assessment' | 'academic_evidence' | 'combination' | 'plan' | 'follow_up' | 'other'>('plan')
  const [actionAgreed, setActionAgreed] = useState('')
  const [followUpDate, setFollowUpDate] = useState('')
  const [learnerVisible, setLearnerVisible] = useState(true)
  const [parentVisible, setParentVisible] = useState(false)

  const studentQuery = useQuery({
    queryKey: ['counselor', 'student', studentId],
    queryFn: () => counselorApi.getStudent(studentId).then((r) => r.data.data),
    enabled: !isNaN(studentId),
  })

  const notesQuery = useQuery({
    queryKey: ['counselor', 'notes'],
    queryFn: () => counselorApi.getNotes().then((r) => r.data.data),
  })

  const studentNotes = (notesQuery.data ?? []).filter(
    (n) => n.student === studentId,
  )

  const createNote = useMutation({
    mutationFn: (body: string) => counselorApi.createNote(studentId, body),
    onSuccess: () => {
      const firstName = studentQuery.data?.student.first_name ?? 'student'
      toast.success(`Note saved for ${firstName}.`)
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'student', studentId] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Something went wrong. Please try again.')
    },
  })

  const updateNote = useMutation({
    mutationFn: ({ noteId, body }: { noteId: number; body: string }) =>
      counselorApi.updateNote(noteId, body),
    onSuccess: () => {
      toast.success('Note updated.')
      setEditingNote(null)
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Something went wrong. Please try again.')
    },
  })

  const deleteNote = useMutation({
    mutationFn: (noteId: number) => counselorApi.deleteNote(noteId),
    onSuccess: () => {
      toast.success('Note removed.')
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'student', studentId] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Something went wrong. Please try again.')
    },
  })

  const createIntervention = useMutation({
    mutationFn: () => counselorApi.createIntervention(studentId, {
      category,
      action_agreed: actionAgreed.trim(),
      follow_up_date: followUpDate || null,
      learner_visible: learnerVisible,
      parent_visible: parentVisible,
    }),
    onSuccess: () => {
      toast.success('Agreed next step saved.')
      setActionAgreed('')
      setFollowUpDate('')
      queryClient.invalidateQueries({ queryKey: ['counselor', 'student', studentId] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'interventions'] })
    },
    onError: () => toast.error('Could not save the agreed next step.'),
  })

  const updateIntervention = useMutation({
    mutationFn: ({ interventionId, status }: { interventionId: number; status: 'open' | 'completed' }) =>
      counselorApi.updateIntervention(interventionId, { status }),
    onSuccess: () => {
      toast.success('Intervention updated.')
      queryClient.invalidateQueries({ queryKey: ['counselor', 'student', studentId] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'interventions'] })
    },
    onError: () => toast.error('Could not update the intervention.'),
  })

  const reviewPlan = useMutation({
    mutationFn: (reviewed: boolean) => counselorApi.reviewPlan(studentId, reviewed)
      .then((response) => response.data.data),
    onSuccess: (result) => {
      queryClient.setQueryData(
        ['counselor', 'student', studentId],
        (current: typeof studentQuery.data) => current?.plan
          ? {
              ...current,
              plan: {
                ...current.plan,
                status: result.status,
              },
            }
          : current,
      )
      queryClient.invalidateQueries({ queryKey: ['counselor', 'students'] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'stats'] })
      toast.success(
        result.status === 'reviewed'
          ? 'Learner plan marked reviewed.'
          : 'Learner plan reopened for review.',
      )
    },
    onError: () => toast.error('Could not update the learner plan review.'),
  })

  if (studentQuery.isLoading) {
    return (
      <div className="counselor-page">
        <div className="student-detail__loading">
          <div className="skeleton-bar skeleton-bar--long" />
          <div className="skeleton-bar skeleton-bar--medium" />
          <div className="skeleton-bar skeleton-bar--short" />
        </div>
      </div>
    )
  }

  if (studentQuery.isError || !studentQuery.data) {
    return (
      <div className="counselor-page">
        <div className="table-empty">
          Could not load student details.{' '}
          <Link to="/counselor/students" className="view-link">
            Back to students
          </Link>
        </div>
      </div>
    )
  }

  const {
    student,
    riasec_result,
    grades,
    attention_reasons: attentionReasons,
    evidence_summary: evidence,
    combination_choices: choices,
    plan,
    interventions,
    academic_progress: academicProgress,
    academic_goals: academicGoals,
    education_goals: educationGoals,
  } = studentQuery.data

  return (
    <div className="counselor-page">
      <div className="student-detail__back">
        <Link to="/counselor/students" className="view-link">
          &larr; Back to students
        </Link>
        <button
          type="button"
          className="btn-primary"
          onClick={() => downloadReport(studentId)}
          disabled={downloadingId !== null}
          style={{ minHeight: 'var(--min-touch-target)' }}
        >
          {downloadingId !== null ? 'Generating…' : 'Download report'}
        </button>
      </div>

      <div className="student-detail">
        {/* Left column */}
        <div className="student-detail__main">
          <StudentDetailHeader student={student} />

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Attention reasons</h2>
            <p className="detail-workspace-card__advisory">
              These are evidence gaps and due actions, not a predictive risk score.
            </p>
            <div className="detail-reason-list">
              {attentionReasons.length > 0 ? attentionReasons.map((reason) => (
                <div key={reason.code}>
                  <strong>{reason.label}</strong>
                  <span>{reason.guidance}</span>
                </div>
              )) : (
                <p>No current attention reasons.</p>
              )}
            </div>
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Evidence summary</h2>
            <div className="detail-evidence-grid">
              <article>
                <span>Academic evidence</span>
                <strong>{evidence.academic.status.replace('_', ' ')}</strong>
                <p>
                  {evidence.academic.subjects_with_evidence} of {evidence.academic.total_subjects} subjects have evidence
                </p>
              </article>
              <article>
                <span>Interest assessment</span>
                <strong>{evidence.assessment.status.replace('_', ' ')}</strong>
                <p>Use this as exploration evidence, not a placement decision.</p>
              </article>
            </div>
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Academic progress</h2>
            <div className="detail-reason-list">
              {academicProgress.subjects.map(subject => (
                <article key={subject.continuity_code}>
                  <div>
                    <strong>{subject.subject_name}</strong>
                    <StatusBadge tone={subject.status === 'strong' || subject.status === 'on_track' ? 'positive' : 'attention'}>
                      {subject.label}
                    </StatusBadge>
                  </div>
                  <p>{subject.explanation}</p>
                  <small>{subject.suggested_action}</small>
                  <section
                    className="detail-progress-evidence"
                    aria-labelledby={`counselor-evidence-${subject.continuity_code}`}
                  >
                    <h3 id={`counselor-evidence-${subject.continuity_code}`}>
                      Evidence used for this status
                    </h3>
                    <ResponsiveDataList
                      ariaLabel={`${subject.subject_name} evidence used for this status`}
                      items={subject.records_used}
                      getKey={(record) => record.id}
                      columns={[
                        {
                          key: 'period',
                          label: 'Period',
                          render: (record) => `Grade ${record.academic_grade}, ${record.year}, Term ${record.term}`,
                        },
                        {
                          key: 'level',
                          label: 'CBE level',
                          render: (record) => GRADE_LEVEL_LABELS[record.level],
                        },
                        {
                          key: 'framework',
                          label: 'Assessment framework',
                          render: (record) => `${record.framework.code} ${record.framework.version}`,
                        },
                        { key: 'origin', label: 'Origin', render: evidenceOrigin },
                        { key: 'verification', label: 'Verification', render: evidenceVerification },
                      ]}
                      empty={<p>No evidence records were used for this status.</p>}
                    />
                  </section>
                </article>
              ))}
            </div>
            <p className="detail-workspace-card__advisory">{academicProgress.advisory_disclaimer}</p>
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Academic targets</h2>
            {academicGoals.length ? academicGoals.map(goal => (
              <article key={goal.id} className="detail-goal-row">
                <strong>{goal.continuity_code}: {goal.current_level.code} to {goal.target_level.code}</strong>
                <p>{goal.action_plan}</p>
                <small>Target: Grade {goal.target_academic_grade}, Term {goal.target_term} {goal.target_year}</small>
              </article>
            )) : <p>No academic targets have been set.</p>}
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Education goals</h2>
            {educationGoals.length ? educationGoals.map(goal => {
              const provenance = goal.programme ?? goal.institution
              const verification = provenance.verification_status === 'historical'
                ? 'Historical'
                : provenance.verification_status === 'verified' ? 'Verified' : 'Unavailable'
              return (
                <article key={goal.id} className="detail-goal-row">
                  <strong>{goal.institution.name}</strong>
                  <p>{goal.programme?.name ?? 'Institution exploration'}</p>
                  <small>
                    {provenance.education_framework} · {provenance.admission_cycle} · Effective {displayDate(provenance.effective_date)} · Verification: {verification}
                    {provenance.verification_status === 'historical' ? ' · Historical reference only' : ''}
                  </small>
                  <a href={provenance.source_url} target="_blank" rel="noreferrer">
                    Open {goal.programme ? 'programme' : 'institution'} source
                  </a>
                </article>
              )
            }) : <p>No education goals have been saved.</p>}
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Saved and provisional choices</h2>
            {choices.length > 0 ? (
              <div className="detail-choice-list">
                {choices.map((choice) => (
                  <article key={choice.id}>
                    <div>
                      <StatusBadge tone={choice.status === 'provisional' ? 'attention' : 'neutral'}>
                        {choice.status === 'provisional' ? 'Provisional' : 'Saved'}
                      </StatusBadge>
                      <span>{choice.code}</span>
                    </div>
                    <h3>{choice.title}</h3>
                    <p>{choice.pathway} · {choice.track}</p>
                    <small>{choice.subjects.join(' · ')}</small>
                  </article>
                ))}
              </div>
            ) : (
              <p>No combinations have been saved.</p>
            )}
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Learner plan</h2>
            {plan ? (
              <>
                <div className="detail-plan-head">
                  <div>
                    <StatusBadge tone={plan.status === 'reviewed' ? 'positive' : 'attention'}>
                      {plan.status.replace(/_/g, ' ')}
                    </StatusBadge>
                    <span>{plan.milestones.filter((item) => item.is_complete).length} of {plan.milestones.length} milestones complete</span>
                  </div>
                  {plan.status !== 'draft' && (
                    <button
                      type="button"
                      className={plan.status === 'reviewed' ? 'btn-ghost' : 'btn-primary'}
                      onClick={() => reviewPlan.mutate(plan.status !== 'reviewed')}
                      disabled={reviewPlan.isPending}
                      aria-label={
                        plan.status === 'reviewed'
                          ? 'Reopen learner plan review'
                          : 'Mark learner plan reviewed'
                      }
                    >
                      {reviewPlan.isPending
                        ? 'Updating...'
                        : plan.status === 'reviewed'
                          ? 'Reopen review'
                          : 'Mark reviewed'}
                    </button>
                  )}
                </div>
                {plan.learner_reason && <blockquote>{plan.learner_reason}</blockquote>}
                <ul className="detail-milestones">
                  {plan.milestones.map((milestone) => (
                    <li key={milestone.id}>
                      <span aria-hidden="true">{milestone.is_complete ? '✓' : '○'}</span>
                      <div>
                        <strong>{milestone.title}</strong>
                        {milestone.due_date && <small>Due {milestone.due_date}</small>}
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p>No learner plan has been started.</p>
            )}
          </section>

          {riasec_result && (
            <section className="student-detail__section">
              <h2 className="student-detail__section-title">RIASEC Assessment</h2>
              <ScoreBars
                scores={riasec_result.scores as Record<RIASECDimension, number>}
              />
              <RecommendationCards
                recommendations={riasec_result.recommendations}
                hollandCode={riasec_result.holland_code}
              />
            </section>
          )}

          <section className="student-detail__section">
            <h2 className="student-detail__section-title">Grades</h2>
            <CounselorGradesTable grades={grades} studentName={student.first_name} />
          </section>

          <section className="student-detail__section detail-workspace-card">
            <h2 className="student-detail__section-title">Intervention timeline</h2>
            <form
              className="intervention-form"
              onSubmit={(event) => {
                event.preventDefault()
                if (actionAgreed.trim()) createIntervention.mutate()
              }}
            >
              <div className="intervention-form__row">
                <label>
                  Category
                  <select value={category} onChange={(event) => setCategory(event.target.value as typeof category)}>
                    <option value="assessment">Interest assessment</option>
                    <option value="academic_evidence">Academic evidence</option>
                    <option value="combination">Subject combination</option>
                    <option value="plan">Learner plan</option>
                    <option value="follow_up">Follow-up</option>
                    <option value="other">Other</option>
                  </select>
                </label>
                <label>
                  Follow-up date
                  <input type="date" value={followUpDate} onChange={(event) => setFollowUpDate(event.target.value)} />
                </label>
              </div>
              <label>
                Agreed next step
                <textarea
                  value={actionAgreed}
                  onChange={(event) => setActionAgreed(event.target.value)}
                  maxLength={2000}
                  rows={3}
                  placeholder="Record the action agreed with the learner"
                />
              </label>
              <div className="intervention-form__visibility">
                <label>
                  <input type="checkbox" checked={learnerVisible} onChange={(event) => setLearnerVisible(event.target.checked)} />
                  Share with learner
                </label>
                <label>
                  <input type="checkbox" checked={parentVisible} onChange={(event) => setParentVisible(event.target.checked)} />
                  Share with approved parent
                </label>
              </div>
              <button type="submit" className="btn-primary" disabled={!actionAgreed.trim() || createIntervention.isPending}>
                {createIntervention.isPending ? 'Saving...' : 'Save agreed next step'}
              </button>
            </form>

            <div className="intervention-timeline">
              {interventions.length > 0 ? interventions.map((intervention) => (
                <article key={intervention.id}>
                  <div>
                    <StatusBadge tone={intervention.status === 'completed' ? 'positive' : 'warning'}>
                      {intervention.status === 'completed' ? 'Completed' : 'Open'}
                    </StatusBadge>
                    <span>{intervention.category.replace('_', ' ')}</span>
                  </div>
                  <strong>{intervention.action_agreed}</strong>
                  <small>{intervention.follow_up_date ? `Follow up ${intervention.follow_up_date}` : 'No follow-up date'}</small>
                  <p>
                    {intervention.learner_visible ? 'Learner visible' : 'Counsellor only'}
                    {intervention.parent_visible ? ' · Parent visible' : ''}
                  </p>
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => updateIntervention.mutate({
                      interventionId: intervention.id,
                      status: intervention.status === 'open' ? 'completed' : 'open',
                    })}
                    disabled={updateIntervention.isPending}
                  >
                    Mark {intervention.status === 'open' ? 'completed' : 'open'}
                  </button>
                </article>
              )) : <p>No interventions recorded yet.</p>}
            </div>
          </section>
        </div>

        {/* Right column */}
        <div className="student-detail__sidebar">
          <div className="quick-info-card">
            <h3 className="quick-info-card__title">Quick Info</h3>
            <dl className="quick-info-card__list">
              <div className="quick-info-card__item">
                <dt>Email</dt>
                <dd>{student.email}</dd>
              </div>
              <div className="quick-info-card__item">
                <dt>County</dt>
                <dd>{student.county ?? 'Not set'}</dd>
              </div>
              <div className="quick-info-card__item">
                <dt>School</dt>
                <dd>{student.school ?? 'Not set'}</dd>
              </div>
              {student.career_interests && (
                <div className="quick-info-card__item">
                  <dt>Career interests</dt>
                  <dd>{student.career_interests}</dd>
                </div>
              )}
              <div className="quick-info-card__item">
                <dt>Joined</dt>
                <dd>
                  {new Date(student.created_at).toLocaleDateString('en-KE', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </dd>
              </div>
            </dl>
          </div>

          <div className="notes-section">
            <h3 className="notes-section__title">
              Counselor Notes
              {studentNotes.length > 0 && (
                <span className="notes-section__count">{studentNotes.length}</span>
              )}
            </h3>

            {editingNote ? (
              <NoteForm
                initialBody={editingNote.body}
                isPending={updateNote.isPending}
                onSubmit={(body) =>
                  updateNote.mutate({ noteId: editingNote.id, body })
                }
                onCancel={() => setEditingNote(null)}
              />
            ) : (
              <NoteForm
                isPending={createNote.isPending}
                onSubmit={(body) => createNote.mutate(body)}
              />
            )}

            {notesQuery.isLoading ? (
              <div className="student-detail__loading">
                <div className="skeleton-bar skeleton-bar--long" />
                <div className="skeleton-bar skeleton-bar--medium" />
              </div>
            ) : studentNotes.length === 0 ? (
              <p className="notes-section__empty">
                No notes yet. Add your first note above.
              </p>
            ) : (
              <div className="notes-section__list">
                {studentNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    onEdit={setEditingNote}
                    onDelete={(noteId) => deleteNote.mutate(noteId)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
