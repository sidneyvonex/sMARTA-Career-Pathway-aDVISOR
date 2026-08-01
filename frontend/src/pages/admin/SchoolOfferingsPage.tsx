import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { guidanceApi, guidanceKeys, type GuidanceCombination } from '../../api/guidance'
import EmptyState from '../../components/common/dashboard/EmptyState'
import DetailDrawer from '../../components/common/management/DetailDrawer'
import ManagementPage from '../../components/common/management/ManagementPage'
import ManagementTable from '../../components/common/management/ManagementTable'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import Pagination from '../../components/common/management/Pagination'
import type { ManagementColumn, PaginationState } from '../../components/common/management/types'
import '../../styles/dashboard.css'
import '../../styles/school-admin.css'

type AvailabilityFilter = 'all' | 'offered' | 'not_offered'

const DEFAULT_PAGE_SIZE: PaginationState['pageSize'] = 25

export default function SchoolOfferingsPage() {
  const queryClient = useQueryClient()
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [initialIds, setInitialIds] = useState<number[]>([])
  const [search, setSearch] = useState('')
  const [pathway, setPathway] = useState('all')
  const [availability, setAvailability] = useState<AvailabilityFilter>('all')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<PaginationState['pageSize']>(DEFAULT_PAGE_SIZE)
  const [detailCombination, setDetailCombination] = useState<GuidanceCombination | null>(null)

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

  const combinations = combinationsQ.data ?? []
  const pathwayOptions = useMemo(() => (
    [...new Set(combinations.map(combination => combination.track.pathway.name))]
      .sort((left, right) => left.localeCompare(right))
  ), [combinations])

  const filteredCombinations = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    return combinations.filter(combination => {
      const isSelected = selectedIds.includes(combination.id)
      const searchableText = [
        combination.code,
        combination.title,
        combination.track.pathway.name,
        combination.track.name,
        ...combination.subjects.map(subject => subject.name),
      ].join(' ').toLowerCase()
      return (
        (!normalizedSearch || searchableText.includes(normalizedSearch))
        && (pathway === 'all' || combination.track.pathway.name === pathway)
        && (availability === 'all'
          || (availability === 'offered' ? isSelected : !isSelected))
      )
    })
  }, [availability, combinations, pathway, search, selectedIds])

  const pageCount = Math.max(1, Math.ceil(filteredCombinations.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const visibleCombinations = filteredCombinations.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  )

  const addedIds = selectedIds.filter(id => !initialIds.includes(id))
  const removedIds = initialIds.filter(id => !selectedIds.includes(id))
  const isDirty = addedIds.length > 0 || removedIds.length > 0

  function toggleCombination(combinationId: number) {
    setSelectedIds(current => (
      current.includes(combinationId)
        ? current.filter(id => id !== combinationId)
        : [...current, combinationId]
    ))
  }

  function updateSearch(value: string) {
    setSearch(value)
    setPage(1)
  }

  function updatePathway(value: string) {
    setPathway(value)
    setPage(1)
  }

  function updateAvailability(value: AvailabilityFilter) {
    setAvailability(value)
    setPage(1)
  }

  const columns: ManagementColumn<GuidanceCombination>[] = [
    {
      key: 'select',
      label: 'Select',
      priority: 'essential',
      align: 'center',
      render: combination => (
        <label className="offering-table__select">
          <input
            className="offering-table__checkbox"
            type="checkbox"
            checked={selectedIds.includes(combination.id)}
            onChange={() => toggleCombination(combination.id)}
            aria-label={`Offer ${combination.title}`}
          />
        </label>
      ),
    },
    {
      key: 'combination',
      label: 'Combination',
      priority: 'identity',
      render: combination => (
        <div className="offering-table__identity">
          <strong>{combination.title}</strong>
          <span>{combination.code}</span>
        </div>
      ),
    },
    {
      key: 'pathway',
      label: 'Pathway and track',
      priority: 'essential',
      render: combination => (
        <div className="offering-table__pathway">
          <strong>{combination.track.pathway.name}</strong>
          <span>{combination.track.name}</span>
        </div>
      ),
    },
    {
      key: 'subjects',
      label: 'Subjects',
      priority: 'secondary',
      render: combination => (
        <span className="offering-table__subjects">
          {combination.subjects.map(subject => <span key={subject.id}>{subject.name}</span>)}
        </span>
      ),
    },
    {
      key: 'availability',
      label: 'Availability',
      priority: 'essential',
      render: combination => selectedIds.includes(combination.id) ? (
        <span className="status-badge status-badge--assessed">Offered</span>
      ) : (
        <span className="status-badge status-badge--pending">Not offered</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      priority: 'secondary',
      render: combination => (
        <span className={`status-badge status-badge--${combination.verification_status === 'verified' ? 'assessed' : 'pending'}`}>
          {combination.verification_status === 'verified' ? 'Verified' : 'Unverified'}
        </span>
      ),
    },
  ]

  const toolbar = (
    <ManagementToolbar
      resultCount={`${filteredCombinations.length} combination${filteredCombinations.length === 1 ? '' : 's'}`}
      search={(
        <label htmlFor="offering-search">
          <span>Search combinations</span>
          <input
            id="offering-search"
            type="search"
            value={search}
            onChange={event => updateSearch(event.target.value)}
            placeholder="Search by code, subject or track"
          />
        </label>
      )}
      filters={(
        <div className="school-offerings-filters">
          <label>
            <span>Pathway</span>
            <select value={pathway} onChange={event => updatePathway(event.target.value)}>
              <option value="all">All pathways</option>
              {pathwayOptions.map(option => <option key={option} value={option}>{option}</option>)}
            </select>
          </label>
          <label>
            <span>Availability</span>
            <select
              value={availability}
              onChange={event => updateAvailability(event.target.value as AvailabilityFilter)}
            >
              <option value="all">All combinations</option>
              <option value="offered">Offered by school</option>
              <option value="not_offered">Not offered</option>
            </select>
          </label>
        </div>
      )}
    />
  )

  return (
    <>
      <ManagementPage
        eyebrow="Curriculum configuration"
        title="School subject offerings"
        description="Select the complete set of active combinations available to Grade 10 learners at your school."
        toolbar={toolbar}
        loading={combinationsQ.isLoading || offeringsQ.isLoading}
        error={combinationsQ.isError || offeringsQ.isError ? {
          title: 'School offerings could not load',
          description: 'The saved offering set is unchanged. Check your connection and try again.',
        } : undefined}
        onRetry={() => {
          combinationsQ.refetch()
          offeringsQ.refetch()
        }}
        errorActionLabel="Retry offerings"
      >
        <div className="school-offerings-tray" aria-label="Offering selection summary">
          <div className="school-offerings-tray__count">
            <strong>{selectedIds.length}</strong>
            <span>selected</span>
          </div>
          <div className="school-offerings-tray__changes" aria-live="polite">
            <span>{addedIds.length} pending addition{addedIds.length === 1 ? '' : 's'}</span>
            <span>{removedIds.length} pending removal{removedIds.length === 1 ? '' : 's'}</span>
          </div>
          <p>Changes are only applied when you save the complete offering set.</p>
          <div className="school-offerings-tray__actions">
            <button
              type="button"
              className="btn-ghost"
              disabled={!isDirty || saveMutation.isPending}
              onClick={() => setSelectedIds(initialIds)}
            >
              Discard changes
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={!isDirty || saveMutation.isPending}
              onClick={() => saveMutation.mutate()}
            >
              {saveMutation.isPending ? 'Saving…' : 'Save offering set'}
            </button>
          </div>
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

        <div className="school-offerings-table">
          <ManagementTable
            ariaLabel="School subject offerings catalogue"
            records={visibleCombinations}
            columns={columns}
            getKey={combination => combination.id}
            getRecordLabel={combination => combination.title}
            getPrimaryAction={combination => ({
              id: 'view',
              label: `View ${combination.title}`,
              shortLabel: 'View',
              onSelect: () => setDetailCombination(combination),
            })}
            getSecondaryActions={() => []}
            empty={(
              <EmptyState
                title={combinations.length ? 'No matching combinations' : 'No active combinations'}
                description={combinations.length
                  ? 'Try a different search, pathway or availability filter.'
                  : 'The current guidance framework does not contain active combinations.'}
              />
            )}
          />
        </div>

        <Pagination
          state={{ page: currentPage, pageSize, total: filteredCombinations.length }}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      </ManagementPage>

      <DetailDrawer
        open={detailCombination !== null}
        title={detailCombination?.title ?? 'Combination details'}
        onClose={() => setDetailCombination(null)}
      >
        {detailCombination && (
          <dl className="offering-details">
            <div><dt>Code</dt><dd>{detailCombination.code}</dd></div>
            <div><dt>Pathway</dt><dd>{detailCombination.track.pathway.name}</dd></div>
            <div><dt>Track</dt><dd>{detailCombination.track.name}</dd></div>
            <div>
              <dt>Subjects</dt>
              <dd>{detailCombination.subjects.map(subject => subject.name).join(', ')}</dd>
            </div>
            <div>
              <dt>School availability</dt>
              <dd>{selectedIds.includes(detailCombination.id) ? 'Offered' : 'Not offered'}</dd>
            </div>
            <div><dt>Verification</dt><dd>{detailCombination.verification_status}</dd></div>
          </dl>
        )}
      </DetailDrawer>
    </>
  )
}
