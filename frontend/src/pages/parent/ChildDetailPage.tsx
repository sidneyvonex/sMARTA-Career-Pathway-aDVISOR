import { useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { parentApi } from '../../api/parent'
import { initials } from '../../lib/format'
import { useDownloadReport } from '../../hooks/useDownloadReport'
import ErrorState from '../../components/common/dashboard/ErrorState'
import LoadingSkeleton from '../../components/common/dashboard/LoadingSkeleton'
import StatusBadge from '../../components/common/dashboard/StatusBadge'
import '../../styles/parent.css'

const DIMENSION_LABELS: Record<string, string> = {
  R: 'Realistic',
  I: 'Investigative',
  A: 'Artistic',
  S: 'Social',
  E: 'Enterprising',
  C: 'Conventional',
}

const PLAN_LABELS = {
  draft: 'Draft',
  ready_for_review: 'Ready for review',
  reviewed: 'Reviewed',
}

export default function ChildDetailPage() {
  const { id } = useParams<{ id: string }>()
  const studentId = Number(id)
  const { downloadReport, downloadingId } = useDownloadReport()
  const detailQ = useQuery({
    queryKey: ['parent-child-detail', studentId],
    queryFn: () => parentApi.getChildDetail(studentId).then((response) => response.data.data),
    enabled: Number.isInteger(studentId) && studentId > 0,
  })

  useEffect(() => {
    if (detailQ.isError) {
      toast.error("Couldn't load your child's profile. Please try again.")
    }
  }, [detailQ.isError])

  if (!Number.isInteger(studentId) || studentId <= 0) {
    return (
      <div className="child-detail">
        <Link to="/" className="child-detail__back" aria-label="Back to dashboard">← Back to dashboard</Link>
        <ErrorState
          title="This learner link is invalid"
          description="Return to the parent dashboard and choose an approved learner."
          secondaryAction={{ label: 'Back to dashboard', to: '/' }}
        />
      </div>
    )
  }
  if (detailQ.isLoading) {
    return <LoadingSkeleton label="Loading learner summary" rows={5} />
  }
  if (detailQ.isError || !detailQ.data) {
    return (
      <ErrorState
        title="Couldn't load profile"
        description="This access may no longer be active, or the connection may have failed."
        onRetry={() => detailQ.refetch()}
        secondaryAction={{ label: 'Back to dashboard', to: '/' }}
      />
    )
  }

  const {
    profile,
    subjects,
    assessment,
    academic_readiness: academic,
    provisional_combination: provisional,
    plan,
    counselor,
    parent_visible_notes: notes,
    interventions = [],
    academic_progress: academicProgress,
    academic_goals: academicGoals = [],
    education_goals: educationGoals = [],
  } = detailQ.data
  const maxScore = assessment ? Math.max(...Object.values(assessment.scores)) : 0
  const completedMilestones = plan?.milestones.filter((item) => item.is_complete).length ?? 0

  return (
    <div className="child-detail">
      <Link to="/" className="child-detail__back" aria-label="Back to dashboard">← Back to dashboard</Link>

      <header className="child-detail__header" aria-labelledby="child-detail-title">
        <div className="child-detail__avatar" aria-hidden="true">
          {initials(profile.first_name, profile.last_name)}
        </div>
        <div className="child-detail__header-copy">
          <span>Learner-approved summary</span>
          <h1 id="child-detail-title">{profile.first_name} {profile.last_name}</h1>
          <p>
            Grade {profile.grade} · {profile.county ?? 'County not recorded'} ·{' '}
            {profile.mode === 'school_linked' ? 'School-linked' : 'Self-guided'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => downloadReport(studentId)}
          disabled={downloadingId === studentId}
        >
          {downloadingId === studentId ? 'Preparing report...' : 'Download report'}
        </button>
      </header>

      <aside className="child-detail__approval" role="note">
        <StatusBadge tone="positive">Learner approved</StatusBadge>
        <p>You are viewing information available through this learner's active parent-access approval.</p>
      </aside>

      <section className="child-detail__section" aria-labelledby="summary-title">
        <SectionTitle eyebrow="Learner summary" title="Interests and context" id="summary-title" />
        <div className="child-detail__summary-grid">
          <div>
            <strong>About</strong>
            <p>{profile.bio || 'No learner summary has been recorded yet.'}</p>
          </div>
          <div>
            <strong>Career interests</strong>
            <p>{profile.career_interests || 'No career interests have been recorded yet.'}</p>
          </div>
        </div>
      </section>

      <section className="child-detail__section" aria-labelledby="interest-title">
        <SectionTitle eyebrow="Interest evidence" title="Career interest profile" id="interest-title" />
        {assessment ? (
          <>
            <div className="child-detail__code">Holland Code: {assessment.holland_code}</div>
            <div className="child-detail__traits">
              {Object.entries(assessment.scores).map(([dimension, score]) => (
                <div className="trait-row" key={dimension}>
                  <span className="trait-row__label">{dimension}</span>
                  <div
                    className="trait-row__bar"
                    role="progressbar"
                    aria-valuenow={score}
                    aria-valuemin={0}
                    aria-valuemax={maxScore}
                    aria-label={DIMENSION_LABELS[dimension] ?? dimension}
                  >
                    <div
                      className="trait-row__fill"
                      style={{ width: `${maxScore > 0 ? (score / maxScore) * 100 : 0}%` }}
                    />
                  </div>
                  <span className="trait-row__score">{score}</span>
                </div>
              ))}
            </div>
            <p className="child-detail__advisory">
              These interest-aligned suggestions are starting points for discussion. They do not predict success or determine placement.
            </p>
            <div className="child-detail__pathways">
              {assessment.recommendations.map((recommendation) => (
                <article key={recommendation.rank}>
                  <span>Explore {recommendation.rank}</span>
                  <h3>{recommendation.pathway.name}</h3>
                  <p>{recommendation.pathway.description}</p>
                  <small>
                    {recommendation.rank === 1
                      ? 'Strongest interest alignment'
                      : 'Suggested for exploration'}
                  </small>
                </article>
              ))}
            </div>
          </>
        ) : (
          <EmptyCopy>{profile.first_name} has not completed the career interest assessment yet.</EmptyCopy>
        )}
      </section>

      <section className="child-detail__section" aria-labelledby="academic-title">
        <SectionTitle eyebrow="Academic evidence" title="Academic readiness" id="academic-title" />
        <div className="child-detail__readiness">
          <StatusBadge tone={academic.status === 'ready' ? 'positive' : 'attention'}>
            {academic.status === 'ready' ? 'Evidence ready' : academic.status === 'in_progress' ? 'In progress' : 'Not started'}
          </StatusBadge>
          <p>
            {academic.subjects_with_evidence} of {academic.total_subjects} enrolled subjects have grade evidence, across {academic.total_grade_records} records.
          </p>
        </div>
        {subjects.length ? (
          <div className="child-detail__subjects">
            {subjects.map((subject) => (
              <article key={subject.id}>
                <div>
                  <h3>{subject.name}</h3>
                  <p>{subject.category}</p>
                </div>
                <div>
                  {subject.grades.length
                    ? subject.grades.map((grade) => (
                        <span className="grade-badge" key={grade.id}>
                          T{grade.term}: {grade.level}
                        </span>
                      ))
                    : <small>No grade evidence</small>}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyCopy>No subjects have been enrolled yet.</EmptyCopy>
        )}
      </section>

      <section className="child-detail__section" aria-labelledby="choice-title">
        <SectionTitle eyebrow="Current direction" title="Provisional combination" id="choice-title" />
        {provisional ? (
          <div className="child-detail__choice">
            <span>{provisional.code}</span>
            <h3>{provisional.title}</h3>
            <p>{provisional.pathway} · {provisional.track}</p>
            <ul>{provisional.subjects.map((subject) => <li key={subject}>{subject}</li>)}</ul>
          </div>
        ) : (
          <EmptyCopy>No provisional combination has been selected.</EmptyCopy>
        )}
      </section>

      {academicProgress && (
        <section className="child-detail__section" aria-labelledby="progress-title">
          <SectionTitle eyebrow="Learner-approved evidence" title="Academic progress" id="progress-title" />
          <div className="child-detail__subjects">
            {academicProgress.subjects.map(subject => (
              <article key={subject.continuity_code}>
                <div>
                  <h3>{subject.subject_name}</h3>
                  <StatusBadge tone={subject.status === 'strong' || subject.status === 'on_track' ? 'positive' : 'attention'}>
                    {subject.label}
                  </StatusBadge>
                </div>
                <div>
                  <p>{subject.explanation}</p>
                  <small>{subject.suggested_action}</small>
                </div>
              </article>
            ))}
          </div>
          <p className="child-detail__advisory">{academicProgress.advisory_disclaimer}</p>
        </section>
      )}

      <section className="child-detail__section" aria-labelledby="academic-goals-title">
        <SectionTitle eyebrow="Learner targets" title="Academic targets" id="academic-goals-title" />
        {academicGoals.length ? (
          <div className="child-detail__subjects">
            {academicGoals.map(goal => (
              <article key={goal.id}>
                <div>
                  <h3>{goal.continuity_code}</h3>
                  <StatusBadge tone="neutral">{goal.status}</StatusBadge>
                </div>
                <div>
                  <p>{goal.action_plan}</p>
                  <small>{goal.current_level.code} to {goal.target_level.code} · Term {goal.target_term} {goal.target_year}</small>
                </div>
              </article>
            ))}
          </div>
        ) : <EmptyCopy>No academic targets have been shared yet.</EmptyCopy>}
      </section>

      <section className="child-detail__section" aria-labelledby="education-goals-title">
        <SectionTitle eyebrow="Exploration choices" title="Education goals" id="education-goals-title" />
        {educationGoals.length ? (
          <div className="child-detail__subjects">
            {educationGoals.map(goal => (
              <article key={goal.id}>
                <div><h3>{goal.institution.name}</h3></div>
                <div>
                  <p>{goal.programme?.name ?? 'Institution exploration'}</p>
                  <small>{goal.institution.education_framework} · {goal.institution.admission_cycle} · {goal.institution.verification_status}</small>
                </div>
              </article>
            ))}
          </div>
        ) : <EmptyCopy>No education goals have been shared yet.</EmptyCopy>}
      </section>

      <section className="child-detail__section" aria-labelledby="plan-title">
        <SectionTitle eyebrow="Action plan" title="Plan milestones" id="plan-title" />
        {plan ? (
          <>
            <div className="child-detail__plan-head">
              <StatusBadge tone={plan.status === 'reviewed' ? 'positive' : 'neutral'}>
                {PLAN_LABELS[plan.status]}
              </StatusBadge>
              <span>{completedMilestones} of {plan.milestones.length} complete</span>
            </div>
            {plan.learner_reason && <p className="child-detail__reason">“{plan.learner_reason}”</p>}
            {plan.milestones.length ? (
              <ul className="child-detail__milestones">
                {plan.milestones.map((milestone) => (
                  <li key={milestone.id}>
                    <span aria-hidden="true">{milestone.is_complete ? '✓' : '○'}</span>
                    <div>
                      <strong>{milestone.title}</strong>
                      {milestone.due_date && <small>Due {formatDate(milestone.due_date)}</small>}
                    </div>
                  </li>
                ))}
              </ul>
            ) : <EmptyCopy>No plan milestones have been added yet.</EmptyCopy>}
          </>
        ) : (
          <EmptyCopy>No learner plan has been started yet.</EmptyCopy>
        )}
      </section>

      <section className="child-detail__section" aria-labelledby="actions-title">
        <SectionTitle eyebrow="Shared actions" title="Agreed next steps" id="actions-title" />
        {interventions.length > 0 ? (
          <div className="child-detail__interventions">
            {interventions.map((intervention) => (
              <article key={intervention.id}>
                <StatusBadge tone={intervention.status === 'completed' ? 'positive' : 'warning'}>
                  {intervention.status === 'completed' ? 'Completed' : 'Open'}
                </StatusBadge>
                <div>
                  <strong>{intervention.action_agreed}</strong>
                  <small>
                    {intervention.follow_up_date
                      ? `Follow up ${new Date(`${intervention.follow_up_date}T00:00:00`).toLocaleDateString('en-KE', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}`
                      : 'No follow-up date'}
                  </small>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyCopy>No agreed actions have been shared with parents yet.</EmptyCopy>
        )}
      </section>

      <section className="child-detail__section" aria-labelledby="notes-title">
        <SectionTitle eyebrow="Shared support" title="Parent-visible notes" id="notes-title" />
        {counselor && (
          <div className="child-detail__counselor">
            <div aria-hidden="true">{initials(counselor.first_name, counselor.last_name)}</div>
            <p>
              <strong>{counselor.first_name} {counselor.last_name}</strong>
              <span>{counselor.email}</span>
            </p>
          </div>
        )}
        {notes.length ? (
          <div className="child-detail__notes">
            {notes.map((note) => (
              <blockquote key={`${note.created_at}-${note.body}`}>
                <p>“{note.body}”</p>
                <footer>{formatDateTime(note.created_at)}</footer>
              </blockquote>
            ))}
          </div>
        ) : (
          <EmptyCopy>No notes have been shared with parents yet.</EmptyCopy>
        )}
      </section>

      <section className="child-detail__report" aria-labelledby="report-title">
        <div>
          <span>Portable summary</span>
          <h2 id="report-title">Download learner report</h2>
          <p>Use the report for a learner-led conversation with the counsellor or school.</p>
        </div>
        <button
          type="button"
          onClick={() => downloadReport(studentId)}
          disabled={downloadingId === studentId}
        >
          {downloadingId === studentId ? 'Preparing report...' : 'Download report'}
        </button>
      </section>
    </div>
  )
}

function SectionTitle({ eyebrow, title, id }: { eyebrow: string; title: string; id: string }) {
  return (
    <header className="child-detail__section-head">
      <span>{eyebrow}</span>
      <h2 id={id}>{title}</h2>
    </header>
  )
}

function EmptyCopy({ children }: { children: React.ReactNode }) {
  return <p className="child-detail__empty">{children}</p>
}

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleDateString('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
