import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import ErrorState from '../components/common/dashboard/ErrorState'
import {
  guidanceApi,
  guidanceKeys,
  type GuidanceCombinationFilters,
} from '../api/guidance'
import '../styles/explorer.css'

const COUNTIES = [
  { value: '', label: 'All five counties' },
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
]

export default function CombinationExplorerPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [pathway, setPathway] = useState('')
  const [track, setTrack] = useState('')
  const [county, setCounty] = useState('')
  const [school, setSchool] = useState('')
  const [locallySaved, setLocallySaved] = useState<Set<number>>(new Set())

  const filters = useMemo<GuidanceCombinationFilters>(() => ({
    ...(search.trim() ? { search: search.trim() } : {}),
    ...(pathway ? { pathway } : {}),
    ...(track ? { track } : {}),
    ...(county ? { county } : {}),
    ...(school ? { school } : {}),
  }), [county, pathway, school, search, track])

  const frameworkQuery = useQuery({
    queryKey: guidanceKeys.framework(),
    queryFn: () => guidanceApi.getFramework(),
  })
  const pathwaysQuery = useQuery({
    queryKey: guidanceKeys.pathways(),
    queryFn: () => guidanceApi.getPathways(),
  })
  const catalogueQuery = useQuery({
    queryKey: guidanceKeys.combinations(),
    queryFn: () => guidanceApi.getCombinations(),
  })
  const combinationsQuery = useQuery({
    queryKey: guidanceKeys.combinations(filters),
    queryFn: () => guidanceApi.getCombinations(filters),
  })
  const choicesQuery = useQuery({
    queryKey: guidanceKeys.learnerChoices(),
    queryFn: () => guidanceApi.getLearnerChoices(),
  })

  const saveMutation = useMutation({
    mutationFn: (combinationId: number) => guidanceApi.saveLearnerChoice(combinationId),
    onSuccess: (response) => {
      const combinationId = response.data.data.combination.id
      setLocallySaved((current) => new Set(current).add(combinationId))
      queryClient.invalidateQueries({ queryKey: guidanceKeys.learnerChoices() })
      queryClient.invalidateQueries({ queryKey: ['student', 'evidence-summary'] })
      toast.success('Combination saved for comparison.')
    },
    onError: () => toast.error('Could not save this combination. Please try again.'),
  })

  const pathways = pathwaysQuery.data?.data.data ?? []
  const combinations = combinationsQuery.data?.data.data ?? []
  const choices = choicesQuery.data?.data.data ?? []
  const selectedPathway = pathways.find((item) => String(item.id) === pathway)
  const availableTracks = selectedPathway?.tracks ?? pathways.flatMap((item) => item.tracks)
  const allSchools = Array.from(
    new Map(
      (catalogueQuery.data?.data.data ?? [])
        .flatMap((item) => item.offered_schools)
        .map((item) => [item.id, item]),
    ).values(),
  ).sort((a, b) => a.name.localeCompare(b.name))
  const savedIds = new Set([
    ...choices.map((choice) => choice.combination.id),
    ...locallySaved,
  ])
  const savedCount = savedIds.size

  const isLoading = (
    frameworkQuery.isLoading ||
    pathwaysQuery.isLoading ||
    catalogueQuery.isLoading ||
    combinationsQuery.isLoading ||
    choicesQuery.isLoading
  )
  const isError = (
    frameworkQuery.isError ||
    pathwaysQuery.isError ||
    catalogueQuery.isError ||
    combinationsQuery.isError ||
    choicesQuery.isError
  )

  function resetFilters() {
    setSearch('')
    setPathway('')
    setTrack('')
    setCounty('')
    setSchool('')
  }

  if (isError) {
    return (
      <ErrorState
        title="The combination catalogue could not load"
        description="Check your connection, then try loading the source-dated pilot catalogue again."
        onRetry={() => {
          frameworkQuery.refetch()
          pathwaysQuery.refetch()
          catalogueQuery.refetch()
          combinationsQuery.refetch()
          choicesQuery.refetch()
        }}
      />
    )
  }

  const framework = frameworkQuery.data?.data.data

  return (
    <div className="explorer-page">
      <header className="explorer-header">
        <div>
          <span className="explorer-kicker">Grade 10 pilot catalogue</span>
          <h1>Explore subject combinations</h1>
          <p>Filter current three-subject options, check where they are offered and save up to three for comparison.</p>
        </div>
        <div className="explorer-saved" aria-live="polite">
          <strong>{savedCount} of 3</strong>
          <span>saved for comparison</span>
        </div>
      </header>

      {framework && (
        <aside className="explorer-source" aria-label="Catalogue source">
          <div>
            <strong>{framework.title}</strong>
            <span>Effective {new Date(`${framework.effective_date}T00:00:00`).toLocaleDateString('en-KE', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}</span>
          </div>
          <a href={framework.source_url} target="_blank" rel="noreferrer">View official source</a>
        </aside>
      )}

      <section className="explorer-filters" aria-label="Combination filters">
        <label>
          <span>Search</span>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Subject, track or code"
          />
        </label>
        <label>
          <span>Pathway</span>
          <select
            value={pathway}
            onChange={(event) => {
              setPathway(event.target.value)
              setTrack('')
            }}
          >
            <option value="">All pathways</option>
            {pathways.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Track</span>
          <select value={track} onChange={(event) => setTrack(event.target.value)}>
            <option value="">All tracks</option>
            {availableTracks.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
        <label>
          <span>County</span>
          <select value={county} onChange={(event) => setCounty(event.target.value)}>
            {COUNTIES.map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>School offering</span>
          <select value={school} onChange={(event) => setSchool(event.target.value)}>
            <option value="">All pilot schools</option>
            {allSchools.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
      </section>

      {isLoading ? (
        <div className="explorer-grid" role="status" aria-label="Loading combinations">
          {Array.from({ length: 4 }, (_, index) => (
            <div className="explorer-card explorer-card--loading" key={index} />
          ))}
        </div>
      ) : combinations.length === 0 ? (
        <section className="explorer-empty">
          <h2>No combinations match these filters</h2>
          <p>Clear the filters or try a broader subject or track search.</p>
          <button type="button" onClick={resetFilters}>Clear filters</button>
        </section>
      ) : (
        <section className="explorer-grid" aria-label="Subject combinations">
          {combinations.map((combination) => {
            const isSaved = savedIds.has(combination.id)
            const cannotSave = savedCount >= 3 && !isSaved
            const isSaving = saveMutation.isPending && saveMutation.variables === combination.id
            return (
              <article className="explorer-card" key={combination.id}>
                <div className="explorer-card__meta">
                  <span>{combination.track.pathway.name}</span>
                  <span>{combination.code}</span>
                </div>
                <h2>{combination.title}</h2>
                <p>{combination.description}</p>
                <div className="explorer-subjects" aria-label="Subjects">
                  {combination.subjects.map((subject) => (
                    <span key={subject.id}>{subject.name}</span>
                  ))}
                </div>
                <div className="explorer-offerings">
                  <strong>{combination.track.name}</strong>
                  <span>
                    {combination.offered_schools.length > 0
                      ? `Offered by ${combination.offered_schools.length} pilot school${combination.offered_schools.length === 1 ? '' : 's'}`
                      : 'No pilot school offering recorded yet'}
                  </span>
                </div>
                <button
                  type="button"
                  className="explorer-save"
                  disabled={isSaved || cannotSave || isSaving}
                  onClick={() => saveMutation.mutate(combination.id)}
                >
                  {isSaved ? 'Saved for comparison' : isSaving ? 'Saving...' : cannotSave ? 'Three saved already' : 'Save combination'}
                </button>
              </article>
            )
          })}
        </section>
      )}
    </div>
  )
}
