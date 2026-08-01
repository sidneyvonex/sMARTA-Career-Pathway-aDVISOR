import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  systemAdminApi,
  type CatalogueCombination,
  type CatalogueData,
} from '../../api/systemAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import ErrorState from '../../components/common/dashboard/ErrorState'
import SectionHeader from '../../components/common/dashboard/SectionHeader'
import Pagination from '../../components/common/management/Pagination'
import type { PaginationState } from '../../components/common/management/types'
import '../../styles/dashboard.css'
import '../../styles/system-admin.css'

type StatusFilter = 'all' | 'active' | 'inactive'

function countLabel(count: number, singular: string, plural: string) {
  return `${count} ${count === 1 ? singular : plural}`
}

export default function SystemAdminCataloguePage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<PaginationState['pageSize']>(25)

  const catalogueQ = useQuery({
    queryKey: ['system-admin', 'catalogue'],
    queryFn: () => systemAdminApi.getCatalogue().then(response => response.data.data),
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) =>
      systemAdminApi.updateCombinationStatus(id, isActive)
        .then(response => response.data.data),
    onSuccess: updated => {
      queryClient.setQueryData<CatalogueData>(
        ['system-admin', 'catalogue'],
        current => current
          ? {
              ...current,
              combinations: current.combinations.map(combination =>
                combination.id === updated.id ? updated : combination,
              ),
            }
          : current,
      )
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['system-admin', 'audit-logs'] })
      toast.success(
        `${updated.title} is now ${updated.is_active ? 'active' : 'inactive'}.`,
      )
    },
    onError: () => {
      toast.error('The combination status could not be updated.')
    },
  })

  const combinations = catalogueQ.data?.combinations ?? []
  const filteredCombinations = useMemo(() => {
    const term = search.trim().toLocaleLowerCase()
    return combinations.filter(combination => {
      const matchesStatus = statusFilter === 'all'
        || (statusFilter === 'active' && combination.is_active)
        || (statusFilter === 'inactive' && !combination.is_active)
      const searchable = [
        combination.code,
        combination.title,
        combination.track.pathway.name,
        combination.track.name,
        ...combination.subjects.map(subject => subject.name),
      ].join(' ').toLocaleLowerCase()
      return matchesStatus && (!term || searchable.includes(term))
    })
  }, [combinations, search, statusFilter])

  useEffect(() => {
    setPage(1)
  }, [search, statusFilter, pageSize])

  const pageCount = Math.max(1, Math.ceil(filteredCombinations.length / pageSize))
  const safePage = Math.min(page, pageCount)
  const pagedCombinations = useMemo(
    () => filteredCombinations.slice((safePage - 1) * pageSize, safePage * pageSize),
    [filteredCombinations, safePage, pageSize],
  )

  const groupedCombinations = useMemo(() => {
    return pagedCombinations.reduce<Record<string, CatalogueCombination[]>>(
      (groups, combination) => {
        const label = combination.track.pathway.name
        groups[label] = [...(groups[label] ?? []), combination]
        return groups
      },
      {},
    )
  }, [pagedCombinations])

  if (catalogueQ.isLoading) {
    return (
      <div className="sysadmin-page catalogue-page" aria-busy="true">
        <div className="skeleton catalogue-page__source-skeleton" />
        <div className="catalogue-grid">
          {[1, 2, 3, 4].map(item => (
            <div className="skeleton catalogue-card catalogue-card--skeleton" key={item} />
          ))}
        </div>
      </div>
    )
  }

  if (catalogueQ.isError || !catalogueQ.data) {
    return (
      <ErrorState
        title="The framework catalogue could not load"
        description="No catalogue status was changed. Check your connection and try again."
        onRetry={() => catalogueQ.refetch()}
        actionLabel="Retry catalogue"
      />
    )
  }

  const { framework } = catalogueQ.data
  if (!framework) {
    return (
      <div className="sysadmin-page catalogue-page">
        <EmptyState
          title="No active framework"
          description="Activate a source-dated framework before managing combinations."
        />
      </div>
    )
  }

  const activeCount = combinations.filter(combination => combination.is_active).length

  return (
    <div className="db-page sysadmin-page catalogue-page">
      <section className="catalogue-source" aria-labelledby="catalogue-title">
        <div>
          <span className="catalogue-source__code">{framework.code}</span>
          <h1 id="catalogue-title">{framework.title}</h1>
          <p>{framework.description}</p>
        </div>
        <dl className="catalogue-source__meta">
          <div>
            <dt>Effective date</dt>
            <dd>{new Date(`${framework.effective_date}T00:00:00`).toLocaleDateString('en-KE', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}</dd>
          </div>
          <div>
            <dt>Catalogue status</dt>
            <dd>{activeCount} of {combinations.length} combinations active</dd>
          </div>
          <a href={framework.source_url} target="_blank" rel="noreferrer">
            Open official source
          </a>
        </dl>
      </section>

      <section aria-labelledby="combination-list-title">
        <SectionHeader
          eyebrow="Pilot controls"
          title="Subject combinations"
          titleId="combination-list-title"
          description="Status changes affect new exploration and selection. Existing learner choices and school records are retained."
        />

        <div className="catalogue-toolbar">
          <label className="catalogue-search">
            <span className="sr-only">Search combinations</span>
            <input
              type="search"
              value={search}
              onChange={event => setSearch(event.target.value)}
              placeholder="Search code, pathway, track or subject"
              aria-label="Search combinations"
            />
          </label>
          <label>
            <span className="sr-only">Filter by status</span>
            <select
              value={statusFilter}
              onChange={event => setStatusFilter(event.target.value as StatusFilter)}
              aria-label="Filter by status"
            >
              <option value="all">All statuses</option>
              <option value="active">Active only</option>
              <option value="inactive">Inactive only</option>
            </select>
          </label>
          <span className="catalogue-toolbar__count" aria-live="polite">
            {countLabel(filteredCombinations.length, 'combination', 'combinations')}
          </span>
        </div>

        {filteredCombinations.length === 0 ? (
          <EmptyState
            title="No combinations match"
            description="Clear the search or choose another status filter."
          />
        ) : (
          <>
          <div className="catalogue-groups">
            {Object.entries(groupedCombinations).map(([pathway, pathwayCombinations]) => (
              <section key={pathway} aria-labelledby={`pathway-${pathway.replace(/\s+/g, '-').toLowerCase()}`}>
                <div className="catalogue-group-heading">
                  <h2 id={`pathway-${pathway.replace(/\s+/g, '-').toLowerCase()}`}>{pathway}</h2>
                  <span>{countLabel(pathwayCombinations.length, 'combination', 'combinations')}</span>
                </div>
                <div className="catalogue-grid">
                  {pathwayCombinations.map(combination => {
                    const isUpdating = statusMutation.isPending
                      && statusMutation.variables?.id === combination.id
                    return (
                      <article className="catalogue-card" key={combination.id}>
                        <div className="catalogue-card__header">
                          <div>
                            <span className="catalogue-card__code">{combination.code}</span>
                            <span className={`sysadmin-badge ${combination.is_active ? 'sysadmin-badge--active' : 'sysadmin-badge--inactive'}`}>
                              {combination.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <span className="catalogue-card__track">{combination.track.name}</span>
                        </div>
                        <h3>{combination.title}</h3>
                        <ul className="catalogue-card__subjects" aria-label={`${combination.title} subjects`}>
                          {combination.subjects.map(subject => (
                            <li key={subject.id}>{subject.name}</li>
                          ))}
                        </ul>
                        <div className="catalogue-card__impact">
                          <span>{countLabel(combination.active_school_count, 'active school', 'active schools')}</span>
                          <span>{countLabel(combination.learner_choice_count, 'learner choice', 'learner choices')}</span>
                        </div>
                        <button
                          type="button"
                          className={`catalogue-card__action${combination.is_active ? ' catalogue-card__action--deactivate' : ''}`}
                          disabled={statusMutation.isPending}
                          onClick={() => statusMutation.mutate({
                            id: combination.id,
                            isActive: !combination.is_active,
                          })}
                          aria-label={`${combination.is_active ? 'Deactivate' : 'Activate'} ${combination.title}`}
                        >
                          {isUpdating
                            ? 'Updating...'
                            : combination.is_active
                              ? 'Deactivate'
                              : 'Activate'}
                        </button>
                      </article>
                    )
                  })}
                </div>
              </section>
            ))}
          </div>
          <Pagination
            state={{ page: safePage, pageSize, total: filteredCombinations.length }}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
          </>
        )}
      </section>
    </div>
  )
}
