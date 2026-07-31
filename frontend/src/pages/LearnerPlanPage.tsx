import { FormEvent, useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  guidanceApi,
  guidanceKeys,
  type LearnerCombinationChoice,
  type LearnerPlan,
  type LearnerPlanUpdate,
  type LearnerPlanStatus,
  type PlanMilestone,
} from '../api/guidance'
import { studentsApi } from '../api/students'
import ErrorState from '../components/common/dashboard/ErrorState'
import '../styles/plan.css'

const STATUS_LABELS: Record<LearnerPlanStatus, string> = {
  draft: 'Draft',
  ready_for_review: 'Ready for review',
  reviewed: 'Reviewed',
}

export default function LearnerPlanPage() {
  const queryClient = useQueryClient()
  const [reason, setReason] = useState('')
  const [milestoneTitle, setMilestoneTitle] = useState('')
  const [dueDate, setDueDate] = useState('')

  const planQuery = useQuery({
    queryKey: guidanceKeys.learnerPlan(),
    queryFn: () => guidanceApi.getLearnerPlan(),
  })
  const choicesQuery = useQuery({
    queryKey: guidanceKeys.learnerChoices(),
    queryFn: () => guidanceApi.getLearnerChoices(),
  })
  const evidenceQuery = useQuery({
    queryKey: ['student', 'evidence-summary'],
    queryFn: () => studentsApi.getEvidenceSummary(),
  })

  const plan = planQuery.data?.data.data ?? null
  const choices = choicesQuery.data?.data.data ?? []
  const provisional = choices.find((choice) => choice.status === 'provisional')
  const evidence = evidenceQuery.data?.data.data

  useEffect(() => {
    if (plan) setReason(plan.learner_reason)
  }, [plan])

  const refreshPlan = () => {
    queryClient.invalidateQueries({ queryKey: guidanceKeys.learnerPlan() })
    queryClient.invalidateQueries({ queryKey: ['student', 'evidence-summary'] })
  }

  const savePlan = useMutation({
    mutationFn: (payload: LearnerPlanUpdate) =>
      guidanceApi.updateLearnerPlan(payload),
    onSuccess: () => {
      refreshPlan()
      toast.success(plan ? 'Plan updated.' : 'Plan started.')
    },
    onError: () => toast.error('Could not save your plan.'),
  })
  const createMilestone = useMutation({
    mutationFn: () => guidanceApi.createPlanMilestone({
      title: milestoneTitle.trim(),
      due_date: dueDate || null,
      position: plan?.milestones.length ?? 0,
    }),
    onSuccess: () => {
      setMilestoneTitle('')
      setDueDate('')
      refreshPlan()
      toast.success('Milestone added.')
    },
    onError: () => toast.error('Could not add that milestone.'),
  })
  const updateMilestone = useMutation({
    mutationFn: ({ milestone, isComplete }: { milestone: PlanMilestone; isComplete: boolean }) =>
      guidanceApi.updatePlanMilestone(milestone.id, { is_complete: isComplete }),
    onSuccess: refreshPlan,
    onError: () => toast.error('Could not update that milestone.'),
  })
  const deleteMilestone = useMutation({
    mutationFn: (milestoneId: number) => guidanceApi.deletePlanMilestone(milestoneId),
    onSuccess: () => {
      refreshPlan()
      toast.success('Milestone removed.')
    },
    onError: () => toast.error('Could not remove that milestone.'),
  })

  const isLoading = planQuery.isLoading || choicesQuery.isLoading || evidenceQuery.isLoading
  if (planQuery.isError || choicesQuery.isError || evidenceQuery.isError) {
    return (
      <ErrorState
        title="Your plan could not load"
        description="Check your connection and try loading your planning evidence again."
        onRetry={() => {
          planQuery.refetch()
          choicesQuery.refetch()
          evidenceQuery.refetch()
        }}
      />
    )
  }
  if (isLoading) {
    return <div className="plan-loading" role="status" aria-label="Loading learner plan"><div /><div /><div /></div>
  }
  if (!provisional) {
    return (
      <section className="plan-empty">
        <span>Start with a provisional choice</span>
        <h1>Your plan needs a combination</h1>
        <p>Compare your saved combinations and mark one as provisional. You can change it as your evidence develops.</p>
        <Link to="/compare">Compare saved choices</Link>
      </section>
    )
  }
  if (!plan) {
    return (
      <section className="plan-start">
        <span>Provisional choice selected</span>
        <h1>Turn your choice into an action plan</h1>
        <ChoiceSummary plan={null} provisional={provisional} />
        <label htmlFor="plan-start-reason">Why are you considering this combination?</label>
        <textarea
          id="plan-start-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          maxLength={1000}
          placeholder="Describe what interests you and what you still want to confirm."
        />
        <button
          type="button"
          disabled={savePlan.isPending}
          onClick={() => savePlan.mutate({ learner_reason: reason })}
        >
          {savePlan.isPending ? 'Starting plan...' : 'Start my plan'}
        </button>
      </section>
    )
  }

  const gaps = [
    ...(evidence?.academic_evidence.status === 'ready' ? [] : ['Complete your academic evidence']),
    ...(evidence?.assessment.status === 'complete' ? [] : ['Complete the career interest assessment']),
    ...(plan.provisional_choice.combination.offered_schools.length ? [] : ['Confirm an offering on the official selection portal']),
    ...(reason.trim() ? [] : ['Record why you are considering this choice']),
  ]
  const completedCount = plan.milestones.filter((item) => item.is_complete).length
  const nextAction = getNextAction(plan, gaps)

  const submitReason = (event: FormEvent) => {
    event.preventDefault()
    savePlan.mutate({ learner_reason: reason })
  }
  const submitMilestone = (event: FormEvent) => {
    event.preventDefault()
    if (milestoneTitle.trim()) createMilestone.mutate()
  }

  return (
    <div className="plan-page">
      <header className="plan-header">
        <div>
          <span>Learner action plan</span>
          <h1>Build evidence around your choice</h1>
          <p>This plan helps you prepare for a review. It does not guarantee placement in a school or combination.</p>
        </div>
        <div className={`plan-status plan-status--${plan.review_status}`}>
          <small>Review status</small>
          <strong>{STATUS_LABELS[plan.review_status]}</strong>
        </div>
      </header>

      <div className="plan-grid">
        <main>
          <ChoiceSummary plan={plan} provisional={provisional} />

          <section className="plan-card" aria-labelledby="plan-reason-title">
            <div className="plan-section-heading">
              <div>
                <span>Your thinking</span>
                <h2 id="plan-reason-title">Why this choice?</h2>
              </div>
              <small>{reason.length}/1000</small>
            </div>
            <form onSubmit={submitReason}>
              <label className="sr-only" htmlFor="plan-reason">Reason for provisional choice</label>
              <textarea
                id="plan-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                maxLength={1000}
                placeholder="Describe what interests you and what you still want to confirm."
              />
              <button type="submit" disabled={savePlan.isPending || reason === plan.learner_reason}>
                {savePlan.isPending ? 'Saving...' : 'Save reason'}
              </button>
            </form>
          </section>

          <section className="plan-card" aria-labelledby="milestones-title">
            <div className="plan-section-heading">
              <div>
                <span>Checklist</span>
                <h2 id="milestones-title">Planning milestones</h2>
              </div>
              <small>{completedCount} of {plan.milestones.length} complete</small>
            </div>
            {plan.milestones.length ? (
              <ul className="plan-milestones">
                {plan.milestones.map((milestone) => (
                  <li key={milestone.id}>
                    <label>
                      <input
                        type="checkbox"
                        checked={milestone.is_complete}
                        disabled={updateMilestone.isPending}
                        onChange={(event) => updateMilestone.mutate({
                          milestone,
                          isComplete: event.target.checked,
                        })}
                      />
                      <span>
                        <strong>{milestone.title}</strong>
                        {milestone.due_date && <small>Due {formatDate(milestone.due_date)}</small>}
                      </span>
                    </label>
                    <button
                      type="button"
                      disabled={deleteMilestone.isPending}
                      onClick={() => deleteMilestone.mutate(milestone.id)}
                      aria-label={`Remove ${milestone.title}`}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="plan-muted">Add a small, specific step you can complete and discuss.</p>
            )}
            <form className="plan-milestone-form" onSubmit={submitMilestone}>
              <label>
                Milestone
                <input
                  id="milestone-title"
                  value={milestoneTitle}
                  onChange={(event) => setMilestoneTitle(event.target.value)}
                  maxLength={160}
                  placeholder="For example, review two pilot schools"
                  required
                />
              </label>
              <label>
                Due date
                <input
                  type="date"
                  value={dueDate}
                  onChange={(event) => setDueDate(event.target.value)}
                />
              </label>
              <button type="submit" disabled={createMilestone.isPending || !milestoneTitle.trim()}>
                {createMilestone.isPending ? 'Adding...' : 'Add milestone'}
              </button>
            </form>
          </section>
        </main>

        <aside className="plan-aside" aria-label="Plan evidence and next action">
          <section className="plan-card">
            <span className="plan-eyebrow">Evidence check</span>
            <h2>{gaps.length ? `${gaps.length} gaps to address` : 'Core evidence ready'}</h2>
            {gaps.length ? (
              <ul className="plan-gaps">{gaps.map((gap) => <li key={gap}>{gap}</li>)}</ul>
            ) : (
              <p className="plan-muted">Your core evidence is ready for a counsellor conversation.</p>
            )}
          </section>

          <section className="plan-next">
            <span>Next action</span>
            <h2>{nextAction.title}</h2>
            <p>{nextAction.description}</p>
            {nextAction.href ? (
              nextAction.href.startsWith('#')
                ? <a href={nextAction.href}>{nextAction.action}</a>
                : <Link to={nextAction.href}>{nextAction.action}</Link>
            ) : (
              <button
                type="button"
                disabled={savePlan.isPending}
                onClick={() => savePlan.mutate({
                  learner_reason: reason,
                  review_status: 'ready_for_review',
                })}
              >
                {savePlan.isPending ? 'Submitting...' : nextAction.action}
              </button>
            )}
          </section>

          {plan.review_status === 'ready_for_review' && (
            <button
              className="plan-return-button"
              type="button"
              disabled={savePlan.isPending}
              onClick={() => savePlan.mutate({ review_status: 'draft' })}
            >
              Return plan to draft
            </button>
          )}
        </aside>
      </div>
    </div>
  )
}

function ChoiceSummary({
  plan,
  provisional,
}: {
  plan: LearnerPlan | null
  provisional: LearnerCombinationChoice
}) {
  const choice = plan?.provisional_choice ?? provisional
  return (
    <section className="plan-choice" aria-labelledby="plan-choice-title">
      <div>
        <span>{choice.combination.code}</span>
        <h2 id="plan-choice-title">{choice.combination.title}</h2>
        <p>{choice.combination.track.pathway.name} · {choice.combination.track.name}</p>
      </div>
      <ul>
        {choice.combination.subjects.map((subject) => <li key={subject.id}>{subject.name}</li>)}
      </ul>
      <Link to="/compare">Review comparison</Link>
    </section>
  )
}

function getNextAction(plan: LearnerPlan, gaps: string[]) {
  if (gaps.length) return {
    title: gaps[0],
    description: 'Address this gap before sending your plan for review.',
    action: gaps[0].includes('academic')
      ? 'Open grades'
      : gaps[0].includes('assessment')
        ? 'Open career quiz'
        : gaps[0].includes('why')
          ? 'Write your reason'
          : 'Review comparison',
    href: gaps[0].includes('academic')
      ? '/grades'
      : gaps[0].includes('assessment')
        ? '/assessment'
        : gaps[0].includes('why')
          ? '#plan-reason'
          : '/compare',
  }
  if (!plan.milestones.length) return {
    title: 'Add your first milestone',
    description: 'Break the choice into one concrete action you can discuss.',
    action: 'Add milestone above',
    href: '#milestone-title',
  }
  if (plan.review_status === 'draft') return {
    title: 'Send your plan for review',
    description: 'Your evidence is ready. A counsellor can help you test the choice.',
    action: 'Mark ready for review',
    href: '',
  }
  return {
    title: plan.review_status === 'reviewed' ? 'Continue your milestones' : 'Prepare for your review',
    description: 'Keep your milestone progress current and bring your questions to the review.',
    action: 'Review comparison',
    href: '/compare',
  }
}

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
