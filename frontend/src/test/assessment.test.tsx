import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LikertQuestion from '../components/assessment/LikertQuestion'
import AssessmentStep from '../components/assessment/AssessmentStep'
import ScoreBars from '../components/assessment/ScoreBars'
import RecommendationCards from '../components/assessment/RecommendationCards'
import AssessmentResultsPage from '../pages/AssessmentResultsPage'
import type { RIASECQuestion, AssessmentRecommendation } from '../api/assessment'

const makeClient = () => new QueryClient({ defaultOptions: { queries: { retry: false } } })

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={makeClient()}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
)

// ── Fixtures ──────────────────────────────────────────────────────────────
const mockQuestion: RIASECQuestion = {
  id: 1, dimension: 'R', text: 'I enjoy fixing things with my hands.', order: 1,
}

const mockQuestions: RIASECQuestion[] = Array.from({ length: 6 }, (_, i) => ({
  id: i + 1,
  dimension: (['R', 'I', 'A', 'S', 'E', 'C'] as const)[i],
  text: `Test question ${i + 1}`,
  order: i + 1,
}))

const mockRecs: AssessmentRecommendation[] = [
  {
    rank: 1,
    pathway: { id: 1, name: 'STEM', description: 'Science and tech.' },
    explanation: {
      summary: 'STEM is suggested because Investigative and Realistic interests lead.',
      leading_dimensions: [
        { code: 'I', label: 'Investigative', score: 22 },
        { code: 'R', label: 'Realistic', score: 18 },
      ],
      limitations: 'This reflects stated interests only. It does not predict success.',
      next_step: 'Review your subjects and available combinations.',
    },
  },
  { rank: 2, pathway: { id: 2, name: 'Social Sciences', description: 'Humanities.' } },
  { rank: 3, pathway: { id: 3, name: 'Arts & Sports Science', description: 'Creative arts.' } },
]

// ── LikertQuestion ────────────────────────────────────────────────────────
describe('LikertQuestion', () => {
  it('renders the question text', () => {
    render(<LikertQuestion question={mockQuestion} questionNumber={1} value={undefined} onChange={() => {}} />, { wrapper: Wrapper })
    expect(screen.getByText('I enjoy fixing things with my hands.')).toBeInTheDocument()
  })

  it('renders exactly 5 buttons', () => {
    render(<LikertQuestion question={mockQuestion} questionNumber={1} value={undefined} onChange={() => {}} />, { wrapper: Wrapper })
    expect(screen.getAllByRole('button')).toHaveLength(5)
  })

  it('calls onChange with correct score when button clicked', () => {
    const onChange = vi.fn()
    render(<LikertQuestion question={mockQuestion} questionNumber={1} value={undefined} onChange={onChange} />, { wrapper: Wrapper })
    fireEvent.click(screen.getByLabelText('Mostly like me'))
    expect(onChange).toHaveBeenCalledWith(1, 4)
  })

  it('marks selected button with aria-pressed=true', () => {
    render(<LikertQuestion question={mockQuestion} questionNumber={1} value={3} onChange={() => {}} />, { wrapper: Wrapper })
    const buttons = screen.getAllByRole('button')
    expect(buttons[2]).toHaveAttribute('aria-pressed', 'true')
    expect(buttons[0]).toHaveAttribute('aria-pressed', 'false')
  })
})

// ── AssessmentStep ────────────────────────────────────────────────────────
describe('AssessmentStep', () => {
  it('renders 6 questions', () => {
    render(
      <AssessmentStep questions={mockQuestions} pageIndex={0} answers={{}} onAnswer={() => {}} />,
      { wrapper: Wrapper }
    )
    expect(screen.getAllByRole('group')).toHaveLength(6)
  })

  it('pre-fills answered questions', () => {
    render(
      <AssessmentStep questions={mockQuestions} pageIndex={0} answers={{ 1: 4 }} onAnswer={() => {}} />,
      { wrapper: Wrapper }
    )
    const buttons = screen.getAllByRole('button')
    // Question 1, button index 3 (score=4) should be pressed
    expect(buttons[3]).toHaveAttribute('aria-pressed', 'true')
  })
})

// ── ScoreBars ─────────────────────────────────────────────────────────────
describe('ScoreBars', () => {
  const scores = { R: 18, I: 22, A: 14, S: 11, E: 16, C: 13 } as const

  it('renders all 6 dimension labels', () => {
    render(<ScoreBars scores={scores} />, { wrapper: Wrapper })
    expect(screen.getByText('Realistic')).toBeInTheDocument()
    expect(screen.getByText('Investigative')).toBeInTheDocument()
    expect(screen.getByText('Artistic')).toBeInTheDocument()
    expect(screen.getByText('Social')).toBeInTheDocument()
    expect(screen.getByText('Enterprising')).toBeInTheDocument()
    expect(screen.getByText('Conventional')).toBeInTheDocument()
  })

  it('renders the highest score value', () => {
    render(<ScoreBars scores={scores} />, { wrapper: Wrapper })
    expect(screen.getByLabelText('22 out of 25')).toBeInTheDocument()
  })
})

// ── RecommendationCards ───────────────────────────────────────────────────
describe('RecommendationCards', () => {
  it('renders 3 pathway cards', () => {
    render(<RecommendationCards recommendations={mockRecs} hollandCode="IRE" />, { wrapper: Wrapper })
    expect(screen.getAllByRole('article')).toHaveLength(3)
  })

  it('displays Holland Code badge', () => {
    render(<RecommendationCards recommendations={mockRecs} hollandCode="IRE" />, { wrapper: Wrapper })
    expect(screen.getByLabelText('Holland Code: IRE')).toBeInTheDocument()
  })

  it('shows pathway names', () => {
    render(<RecommendationCards recommendations={mockRecs} hollandCode="IRE" />, { wrapper: Wrapper })
    expect(screen.getByText('STEM')).toBeInTheDocument()
    expect(screen.getByText('Social Sciences')).toBeInTheDocument()
    expect(screen.getByText('Arts & Sports Science')).toBeInTheDocument()
  })

  it('presents ranked interest alignment without exposing fit percentages', () => {
    render(<RecommendationCards recommendations={mockRecs} hollandCode="IRE" />, { wrapper: Wrapper })
    expect(screen.getByText('Strongest interest alignment')).toBeInTheDocument()
    expect(screen.getAllByText('Suggested for exploration')).toHaveLength(2)
    expect(screen.queryByText(/73%|59%|match/i)).not.toBeInTheDocument()
  })

  it('explains that pathway suggestions are advisory', () => {
    render(<RecommendationCards recommendations={mockRecs} hollandCode="IRE" />, { wrapper: Wrapper })
    expect(screen.getByText(/starting points for exploration/i)).toBeInTheDocument()
    expect(screen.getByText(/do not predict success or decide placement/i)).toBeInTheDocument()
  })

  it('shows the saved explanation for a pathway', () => {
    render(<RecommendationCards recommendations={mockRecs} hollandCode="IRE" />, { wrapper: Wrapper })
    expect(screen.getByText(/suggested because investigative and realistic interests/i)).toBeInTheDocument()
  })
})

describe('AssessmentResultsPage', () => {
  it('separates interests, missing evidence and the next action', async () => {
    render(<AssessmentResultsPage />, { wrapper: Wrapper })

    expect(await screen.findByRole('heading', { name: 'Your stated interests' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Pathways to explore' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Missing evidence' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Your next step' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Review my evidence' })).toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: 'Assessment method record' })).toHaveTextContent(
      'riasec-pilot-1.0',
    )
    expect(screen.getByRole('complementary', { name: 'Assessment method record' })).toHaveTextContent(
      'interest-alignment-1.0',
    )
    expect(screen.queryByText(/chance of success|success probability/i)).not.toBeInTheDocument()
  })
})
