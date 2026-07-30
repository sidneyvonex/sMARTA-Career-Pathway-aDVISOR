import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
  const queryClient = useQueryClient()
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
      queryClient.invalidateQueries({ queryKey: ['assessment-latest'] })
      toast.success('Assessment complete.')
      navigate('/assessment/results')
    },
    onError: () => {
      toast.error("No connection. Your answers are saved — try again when you're back online.")
    },
  })

  const questions = questionsRes?.data.data ?? []
  const pages = Array.from({ length: TOTAL_PAGES }, (_, index) =>
    questions.slice(index * PER_PAGE, index * PER_PAGE + PER_PAGE)
  )
  const currentPageQuestions = pages[pageIndex] ?? []
  const currentPageAnswered = currentPageQuestions.every((question) => answers[question.id] !== undefined)
  const isLastPage = pageIndex === TOTAL_PAGES - 1
  const progressPct = ((pageIndex + 1) / TOTAL_PAGES) * 100
  const answeredCount = Object.keys(answers).length

  function handleAnswer(questionId: number, score: number) {
    const next = { ...answers, [questionId]: score }
    setAnswers(next)
    saveDraft(next)
  }

  function handleNext() {
    if (isLastPage) {
      const responses: ResponseItem[] = Object.entries(answers).map(([questionId, score]) => ({
        question_id: Number(questionId),
        score,
      }))
      submitMutation.mutate(responses)
    } else {
      setPageIndex((page) => page + 1)
      window.scrollTo(0, 0)
    }
  }

  function handleBack() {
    setPageIndex((page) => page - 1)
    window.scrollTo(0, 0)
  }

  if (isLoading) {
    return <div className="assessment-state">Preparing your questions…</div>
  }

  if (isError) {
    return <div className="assessment-state assessment-state--error">We could not load the questions. Check your connection and refresh.</div>
  }

  return (
    <div className="assessment-page">
      <header className="assessment-hero">
        <div>
          <span className="assessment-eyebrow">Career discovery</span>
          <h1>What feels like you?</h1>
          <p>There are no right answers. Choose the response that sounds most natural to you.</p>
        </div>
        <div className="assessment-hero__badge" aria-hidden="true">
          <span>R</span><span>I</span><span>A</span>
          <span>S</span><span>E</span><span>C</span>
        </div>
      </header>

      <div className="assessment-layout">
        <aside className="assessment-journey" aria-label="Assessment progress">
          <span className="assessment-eyebrow">Your progress</span>
          <strong>{Math.round(progressPct)}%</strong>
          <p>Page {pageIndex + 1} of {TOTAL_PAGES}</p>
          <div
            className="assessment-progress-bar"
            role="progressbar"
            aria-valuenow={pageIndex + 1}
            aria-valuemin={1}
            aria-valuemax={TOTAL_PAGES}
            aria-label={`Page ${pageIndex + 1} of ${TOTAL_PAGES}`}
          >
            <div className="assessment-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
          <div className="assessment-journey__steps" aria-hidden="true">
            {Array.from({ length: TOTAL_PAGES }, (_, index) => (
              <span key={index} className={index <= pageIndex ? 'is-active' : ''}>{index + 1}</span>
            ))}
          </div>
          <small>{answeredCount} of {questions.length} statements answered</small>
        </aside>

        <section className="assessment-card">
          <div className="assessment-card__heading">
            <span>Part {pageIndex + 1}</span>
            <h2>Rate each statement</h2>
          </div>
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
                className="assessment-button assessment-button--secondary"
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
              className="assessment-button"
              onClick={handleNext}
              disabled={!currentPageAnswered || submitMutation.isPending}
            >
              {submitMutation.isPending ? 'Submitting…' : isLastPage ? 'See my results' : 'Next →'}
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
