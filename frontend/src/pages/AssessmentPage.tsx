import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import AssessmentStep from '../components/assessment/AssessmentStep'
import { assessmentApi } from '../api/assessment'
import type { ResponseItem } from '../api/assessment'
import '../styles/assessment.css'

const DRAFT_KEY = 'riasec_draft'
const TOTAL_PAGES = 5
const PER_PAGE = 6

function loadDraft(): Record<number, number> {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveDraft(answers: Record<number, number>) {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(answers))
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
}

export default function AssessmentPage() {
  const navigate = useNavigate()
  const [pageIndex, setPageIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>(loadDraft)

  const { data: questionsRes, isLoading, isError } = useQuery({
    queryKey: ['assessment-questions'],
    queryFn: () => assessmentApi.getQuestions(),
    staleTime: Infinity,
  })

  const submitMutation = useMutation({
    mutationFn: (responses: ResponseItem[]) => assessmentApi.submitAssessment(responses),
    onSuccess: () => {
      clearDraft()
      toast.success('Assessment complete!')
      navigate('/assessment/results')
    },
    onError: () => {
      toast.error("No connection. Your answers are saved — try again when you're back online.")
    },
  })

  const questions = questionsRes?.data.data ?? []
  const pages = Array.from({ length: TOTAL_PAGES }, (_, i) =>
    questions.slice(i * PER_PAGE, i * PER_PAGE + PER_PAGE)
  )
  const currentPageQuestions = pages[pageIndex] ?? []
  const currentPageAnswered = currentPageQuestions.every((q) => answers[q.id] !== undefined)
  const isLastPage = pageIndex === TOTAL_PAGES - 1
  const progressPct = ((pageIndex + 1) / TOTAL_PAGES) * 100

  function handleAnswer(questionId: number, score: number) {
    const next = { ...answers, [questionId]: score }
    setAnswers(next)
    saveDraft(next)
  }

  function handleNext() {
    if (isLastPage) {
      const responses: ResponseItem[] = Object.entries(answers).map(([qid, score]) => ({
        question_id: Number(qid),
        score,
      }))
      submitMutation.mutate(responses)
    } else {
      setPageIndex((p) => p + 1)
      window.scrollTo(0, 0)
    }
  }

  function handleBack() {
    setPageIndex((p) => p - 1)
    window.scrollTo(0, 0)
  }

  if (isLoading) {
    return (
      <div className="assessment-page">
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading questions…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="assessment-page">
        <p style={{ color: 'var(--color-text-secondary)' }}>
          Failed to load questions. Please check your connection and refresh.
        </p>
      </div>
    )
  }

  return (
    <div className="assessment-page">
      <div className="assessment-progress">
        <p className="assessment-progress-label">
          Page {pageIndex + 1} of {TOTAL_PAGES}
        </p>
        <div className="assessment-progress-bar">
          <div className="assessment-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      <div className="assessment-card">
        <AssessmentStep
          questions={currentPageQuestions}
          pageIndex={pageIndex}
          answers={answers}
          onAnswer={handleAnswer}
        />

        <div className="assessment-nav">
          {pageIndex > 0 ? (
            <button
              type="button"
              className="btn-ghost"
              onClick={handleBack}
              disabled={submitMutation.isPending}
            >
              ← Back
            </button>
          ) : (
            <span />
          )}
          <button
            type="button"
            className="btn-primary"
            onClick={handleNext}
            disabled={!currentPageAnswered || submitMutation.isPending}
            style={{ minHeight: 'var(--min-touch-target, 44px)' }}
          >
            {submitMutation.isPending
              ? 'Submitting…'
              : isLastPage
              ? 'Submit'
              : 'Next →'}
          </button>
        </div>
      </div>
    </div>
  )
}
