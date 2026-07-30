import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { guidanceApi, guidanceKeys, type GuidanceCombination } from '../../api/guidance'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ErrorState from '../../components/common/dashboard/ErrorState'
import SectionHeader from '../../components/common/dashboard/SectionHeader'
import '../../styles/dashboard.css'
import '../../styles/school-admin.css'

interface TrackGroup {
  name: string
  combinations: GuidanceCombination[]
}

interface PathwayGroup {
  name: string
  tracks: TrackGroup[]
}

export default function SchoolOfferingsPage() {
  const queryClient = useQueryClient()
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [initialIds, setInitialIds] = useState<number[]>([])

  const combinationsQ = useQuery({
    queryKey: guidanceKeys.combinations(),
    queryFn: () => guidanceApi.getCombinations().then(response => response.data.data),
  })
  const offeringsQ = useQuery({
    queryKey: guidanceKeys.schoolOfferings(),
    queryFn: () => guidanceApi.getSchoolOfferings().then(response => response.data.data),
  })

  useEffect(() => {
    if (offeringsQ.data) {
      setSelectedIds(offeringsQ.data.combination_ids)
      setInitialIds(offeringsQ.data.combination_ids)
    }
  }, [offeringsQ.data])

  const saveMutation = useMutation({
    mutationFn: () => guidanceApi.replaceSchoolOfferings(selectedIds),
    onSuccess: response => {
      const saved = response.data.data.combination_ids
      setSelectedIds(saved)
      setInitialIds(saved)
      queryClient.setQueryData(guidanceKeys.schoolOfferings(), response.data.data)
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      toast.success(response.data.message)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message ?? 'Could not update school offerings.')
    },
  })

  const groups = useMemo<PathwayGroup[]>(() => {
    const pathways = new Map<string, Map<string, GuidanceCombination[]>>()
    for (const combination of combinationsQ.data ?? []) {
      const pathwayName = combination.track.pathway.name
      const trackName = combination.track.name
      if (!pathways.has(pathwayName)) pathways.set(pathwayName, new Map())
      const tracks = pathways.get(pathwayName)!
      tracks.set(trackName, [...(tracks.get(trackName) ?? []), combination])
    }
    return [...pathways.entries()].map(([name, tracks]) => ({
      name,
      tracks: [...tracks.entries()].map(([trackName, combinations]) => ({
        name: trackName,
        combinations,
      })),
    }))
  }, [combinationsQ.data])

  if (combinationsQ.isLoading || offeringsQ.isLoading) {
    return <p className="loading-text">Loading school offerings…</p>
  }
  if (combinationsQ.isError || offeringsQ.isError) {
    return (
      <ErrorState
        title="School offerings could not load"
        description="The saved offering set is unchanged. Check your connection and try again."
        onRetry={() => {
          combinationsQ.refetch()
          offeringsQ.refetch()
        }}
        actionLabel="Retry offerings"
        secondaryAction={{ label: 'Return to dashboard', to: '/' }}
      />
    )
  }

  const removedIds = initialIds.filter(id => !selectedIds.includes(id))
  const isDirty = (
    selectedIds.length !== initialIds.length
    || selectedIds.some(id => !initialIds.includes(id))
  )

  function toggleCombination(combinationId: number) {
    setSelectedIds(current => (
      current.includes(combinationId)
        ? current.filter(id => id !== combinationId)
        : [...current, combinationId]
    ))
  }

  return (
    <div className="school-offerings-page">
      <SectionHeader
        eyebrow="Curriculum configuration"
        title="School subject offerings"
        description="Select the complete set of active combinations available to Grade 10 learners at your school."
      />

      <div className="school-offerings-page__summary">
        <div>
          <strong>{selectedIds.length}</strong>
          <span>combinations selected</span>
        </div>
        <p>
          Saving replaces the complete school offering set. Each option contains exactly three elective subjects.
        </p>
        <button
          type="button"
          className="btn-primary"
          disabled={!isDirty || saveMutation.isPending}
          onClick={() => saveMutation.mutate()}
        >
          {saveMutation.isPending ? 'Saving…' : 'Save offering set'}
        </button>
      </div>

      {removedIds.length > 0 && (
        <div className="school-offerings-warning" role="alert">
          <strong>Review learner impact before saving</strong>
          <p>
            Removing an offering can affect learners who saved or selected that combination.
            Counsellors should review affected provisional choices after this update.
          </p>
        </div>
      )}

      {groups.length ? groups.map(pathway => (
        <section className="offering-pathway" key={pathway.name}>
          <h2>{pathway.name}</h2>
          {pathway.tracks.map(track => (
            <div className="offering-track" key={track.name}>
              <h3>{track.name}</h3>
              <div className="offering-grid">
                {track.combinations.map(combination => (
                  <label
                    className={`offering-card${selectedIds.includes(combination.id) ? ' offering-card--selected' : ''}`}
                    key={combination.id}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(combination.id)}
                      onChange={() => toggleCombination(combination.id)}
                      aria-label={`Offer ${combination.title}`}
                    />
                    <span className="offering-card__code">{combination.code}</span>
                    <strong>{combination.title}</strong>
                    <span className="offering-card__subjects">
                      {combination.subjects.map(subject => (
                        <span key={subject.id}>{subject.name}</span>
                      ))}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </section>
      )) : (
        <EmptyState
          title="No active combinations"
          description="The current guidance framework does not contain active combinations."
        />
      )}
    </div>
  )
}
