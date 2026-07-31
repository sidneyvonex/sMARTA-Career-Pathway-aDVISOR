import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { assessmentApi } from '../api/assessment'
import { guidanceApi, guidanceKeys } from '../api/guidance'
import { studentsApi } from '../api/students'
import ErrorState from '../components/common/dashboard/ErrorState'
import '../styles/compare.css'

const COUNTIES = [
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
]

export default function CombinationComparePage() {
  const queryClient = useQueryClient()
  const choicesQuery = useQuery({
    queryKey: guidanceKeys.learnerChoices(),
    queryFn: () => guidanceApi.getLearnerChoices(),
  })
  const evidenceQuery = useQuery({
    queryKey: ['student', 'evidence-summary'],
    queryFn: () => studentsApi.getEvidenceSummary(),
  })
  const assessmentQuery = useQuery({
    queryKey: ['assessment-latest'],
    queryFn: () => assessmentApi.getLatest(),
    retry: false,
  })
  const provisionalMutation = useMutation({
    mutationFn: (choiceId: number) => guidanceApi.setProvisionalChoice(choiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guidanceKeys.learnerChoices() })
      queryClient.invalidateQueries({ queryKey: ['student', 'evidence-summary'] })
      toast.success('Provisional combination updated.')
    },
    onError: () => toast.error('Could not update your provisional choice.'),
  })

  const isLoading = (
    choicesQuery.isLoading ||
    evidenceQuery.isLoading ||
    assessmentQuery.isLoading
  )
  if (choicesQuery.isError || evidenceQuery.isError) {
    return (
      <ErrorState
        title="Your comparison could not load"
        description="Check your connection and try loading your saved combinations again."
        onRetry={() => {
          choicesQuery.refetch()
          evidenceQuery.refetch()
          assessmentQuery.refetch()
        }}
      />
    )
  }

  const choices = choicesQuery.data?.data.data ?? []
  const evidence = evidenceQuery.data?.data.data
  const assessment = assessmentQuery.data?.data.data

  if (!isLoading && choices.length < 2) {
    return (
      <section className="compare-empty">
        <span>Comparison needs two choices</span>
        <h1>Save at least two combinations</h1>
        <p>Explore the pilot catalogue and save two or three combinations before comparing them side by side.</p>
        <Link to="/explore">Explore combinations</Link>
      </section>
    )
  }

  if (isLoading) {
    return (
      <div className="compare-loading" role="status" aria-label="Loading comparison">
        {Array.from({ length: 3 }, (_, index) => <div key={index} />)}
      </div>
    )
  }

  return (
    <div className="compare-page">
      <header className="compare-header">
        <div>
          <span>Evidence-led comparison</span>
          <h1>Compare your saved combinations</h1>
          <p>Use the same evidence for each option. This comparison supports a provisional choice, not a final placement decision.</p>
        </div>
        <Link to="/explore">Edit saved choices</Link>
      </header>

      <section className="compare-section compare-section--identity" aria-labelledby="compare-options">
        <h2 id="compare-options">Your options</h2>
        <div className="compare-columns">
          {choices.map((choice) => (
            <article className="compare-option" key={choice.id}>
              <span>{choice.combination.code}</span>
              <h3>{choice.combination.title}</h3>
              <p>{choice.combination.description}</p>
              <button
                type="button"
                disabled={choice.status === 'provisional' || provisionalMutation.isPending}
                onClick={() => provisionalMutation.mutate(choice.id)}
              >
                {choice.status === 'provisional' ? 'Current provisional choice' : 'Make provisional'}
              </button>
            </article>
          ))}
        </div>
      </section>

      <ComparisonSection title="Pathway and track">
        {choices.map((choice) => (
          <ComparisonItem key={choice.id} title={choice.combination.track.pathway.name}>
            <p>{choice.combination.track.name}</p>
          </ComparisonItem>
        ))}
      </ComparisonSection>

      <ComparisonSection title="Three elective subjects">
        {choices.map((choice) => (
          <ComparisonItem key={choice.id} title={choice.combination.code}>
            <ul>
              {choice.combination.subjects.map((subject) => (
                <li key={subject.id}>{subject.name}</li>
              ))}
            </ul>
          </ComparisonItem>
        ))}
      </ComparisonSection>

      <ComparisonSection title="Interest evidence">
        {choices.map((choice) => {
          const recommendation = assessment?.recommendations.find(
            (item) => item.pathway.id === choice.combination.track.pathway.id,
          )
          return (
            <ComparisonItem
              key={choice.id}
              title={recommendation
                ? recommendation.rank === 1
                  ? 'Strongest current alignment'
                  : `Exploration suggestion ${recommendation.rank}`
                : 'Not covered by latest result'}
            >
              <p>
                {recommendation?.explanation?.summary ??
                  'Your latest interest assessment does not provide specific evidence for this pathway.'}
              </p>
            </ComparisonItem>
          )
        })}
      </ComparisonSection>

      <ComparisonSection title="Academic evidence">
        {choices.map((choice) => (
          <ComparisonItem
            key={choice.id}
            title={evidence?.academic_evidence.status === 'ready' ? 'Evidence ready' : 'Evidence incomplete'}
          >
            <p>
              {evidence
                ? `${evidence.academic_evidence.subjects_with_evidence} of ${evidence.academic_evidence.total_subjects} enrolled subjects have grade evidence.`
                : 'Academic evidence is not available.'}
            </p>
          </ComparisonItem>
        ))}
      </ComparisonSection>

      <ComparisonSection title="Pilot school offerings">
        {choices.map((choice) => (
          <ComparisonItem key={choice.id} title={`${choice.combination.offered_schools.length} schools recorded`}>
            <div className="compare-counties">
              {COUNTIES.map((county) => {
                const schools = choice.combination.offered_schools.filter(
                  (item) => item.county === county.value,
                )
                return (
                  <p key={county.value}>
                    <strong>{county.label}</strong>
                    <span>{schools.length ? schools.map((item) => item.name).join(', ') : 'Not recorded'}</span>
                  </p>
                )
              })}
            </div>
          </ComparisonItem>
        ))}
      </ComparisonSection>

      <ComparisonSection title="Related routes and careers">
        {choices.map((choice) => (
          <ComparisonItem key={choice.id} title={choice.combination.track.name}>
            {choice.combination.related_routes.length ? (
              <ul>
                {choice.combination.related_routes.map((route) => <li key={route}>{route}</li>)}
              </ul>
            ) : (
              <p>No curated related routes are recorded.</p>
            )}
          </ComparisonItem>
        ))}
      </ComparisonSection>

      <ComparisonSection title="Evidence gaps">
        {choices.map((choice) => {
          const gaps = [
            ...(assessment ? [] : ['Complete the interest assessment']),
            ...(evidence?.academic_evidence.status === 'ready' ? [] : ['Complete academic evidence']),
            ...(choice.combination.offered_schools.length ? [] : ['Confirm a pilot school offering']),
          ]
          return (
            <ComparisonItem key={choice.id} title={gaps.length ? `${gaps.length} gaps to review` : 'No current evidence gaps'}>
              {gaps.length ? <ul>{gaps.map((gap) => <li key={gap}>{gap}</li>)}</ul> : <p>Review this evidence with a counsellor before planning.</p>}
            </ComparisonItem>
          )
        })}
      </ComparisonSection>

      <footer className="compare-source">
        <strong>Source date</strong>
        <span>
          {choices[0]?.combination.framework.title}, effective{' '}
          {choices[0] ? new Date(`${choices[0].combination.framework.effective_date}T00:00:00`).toLocaleDateString('en-KE') : ''}
        </span>
        {choices[0] && <a href={choices[0].combination.framework.source_url} target="_blank" rel="noreferrer">Open official source</a>}
      </footer>
    </div>
  )
}

function ComparisonSection({ title, children }: { title: string; children: React.ReactNode }) {
  const sectionId = `compare-${title.toLowerCase().replace(/[^a-z]+/g, '-')}`
  return (
    <section className="compare-section" aria-labelledby={sectionId}>
      <h2 id={sectionId}>{title}</h2>
      <div className="compare-columns">{children}</div>
    </section>
  )
}

function ComparisonItem({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <article className="compare-item">
      <h3>{title}</h3>
      {children}
    </article>
  )
}
