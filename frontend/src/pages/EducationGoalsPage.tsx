import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import {
  tertiaryApi,
  type CatalogueFilters,
  type EducationGoalKind,
  type Institution,
  type Programme,
} from '../api/tertiary'
import EmptyState from '../components/common/dashboard/EmptyState'
import ErrorState from '../components/common/dashboard/ErrorState'
import LoadingSkeleton from '../components/common/dashboard/LoadingSkeleton'
import EducationGoalList from '../components/students/EducationGoalList'
import ProgrammeReferenceDetail from '../components/students/ProgrammeReferenceDetail'
import { educationGoalKeys, useEducationGoalMutations } from '../hooks/useEducationGoalMutations'

import '../styles/student-pages.css'


function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(value))
}


export default function EducationGoalsPage() {
  const [institutionSearch, setInstitutionSearch] = useState('')
  const [county, setCounty] = useState('')
  const [framework, setFramework] = useState('')
  const [cycle, setCycle] = useState('')
  const [verificationStatus, setVerificationStatus] = useState<CatalogueFilters['verification_status'] | ''>('')
  const [catalogueInstitutions, setCatalogueInstitutions] = useState<Institution[]>([])
  const [selectedInstitution, setSelectedInstitution] = useState<Institution | null>(null)
  const [programmeSearch, setProgrammeSearch] = useState('')
  const [selectedProgramme, setSelectedProgramme] = useState<Programme | null>(null)
  const [selectionNotice, setSelectionNotice] = useState('')
  const [goalScope, setGoalScope] = useState<'institution' | 'programme'>('institution')
  const [goalSlot, setGoalSlot] = useState('primary')

  const goalsQ = useQuery({
    queryKey: educationGoalKeys.all,
    queryFn: () => tertiaryApi.getEducationGoals().then((response) => response.data.data),
  })
  const institutionsQ = useQuery({
    queryKey: ['tertiary', 'institutions', institutionSearch, county, framework, cycle, verificationStatus],
    queryFn: () => tertiaryApi.getInstitutions({
      search: institutionSearch,
      county,
      framework,
      cycle,
      verification_status: verificationStatus || undefined,
    }).then((response) => response.data.data),
  })
  const programmesQ = useQuery({
    queryKey: ['tertiary', 'programmes', selectedInstitution?.id, programmeSearch],
    queryFn: () => tertiaryApi.getProgrammes({
      institution: selectedInstitution!.id,
      search: programmeSearch,
    }).then((response) => response.data.data),
    enabled: selectedInstitution !== null,
  })
  const detailQ = useQuery({
    queryKey: ['tertiary', 'programme', selectedProgramme?.id],
    queryFn: () => tertiaryApi.getProgramme(selectedProgramme!.id).then((response) => response.data.data),
    enabled: selectedProgramme !== null,
  })
  const { create } = useEducationGoalMutations()

  const usedSlots = useMemo(() => new Set((goalsQ.data ?? []).map((goal) => (
    goal.kind === 'primary' ? 'primary' : `alternative-${goal.priority}`
  ))), [goalsQ.data])
  const facetOptions = useMemo(() => ({
    counties: [...new Set(catalogueInstitutions.map((institution) => institution.county))].sort(),
    frameworks: [...new Set(catalogueInstitutions.map((institution) => institution.education_framework))].sort(),
    cycles: [...new Set(catalogueInstitutions.map((institution) => institution.admission_cycle))].sort(),
    verificationStatuses: [...new Set(catalogueInstitutions.map((institution) => institution.verification_status))].sort(),
  }), [catalogueInstitutions])

  useEffect(() => {
    if (!institutionsQ.isSuccess) return
    if (institutionsQ.data.length > 0) {
      setCatalogueInstitutions((current) => {
        const merged = new Map(current.map((institution) => [institution.id, institution]))
        institutionsQ.data.forEach((institution) => merged.set(institution.id, institution))
        return [...merged.values()]
      })
    }
    if (selectedInstitution && !institutionsQ.data.some(({ id }) => id === selectedInstitution.id)) {
      setSelectedInstitution(null)
      setSelectedProgramme(null)
      setProgrammeSearch('')
      setGoalScope('institution')
      setSelectionNotice('Institution selection cleared because it no longer matches the catalogue filters.')
    }
  }, [institutionsQ.data, institutionsQ.isSuccess, selectedInstitution])

  useEffect(() => {
    if (!programmesQ.isSuccess || !selectedProgramme) return
    if (!programmesQ.data.some(({ id }) => id === selectedProgramme.id)) {
      setSelectedProgramme(null)
      setGoalScope('institution')
      setSelectionNotice('Programme selection cleared because it no longer matches the programme search.')
    }
  }, [programmesQ.data, programmesQ.isSuccess, selectedProgramme])

  useEffect(() => {
    const firstOpen = ['primary', 'alternative-1', 'alternative-2'].find((slot) => !usedSlots.has(slot))
    if (usedSlots.has(goalSlot) && firstOpen) setGoalSlot(firstOpen)
  }, [goalSlot, usedSlots])

  const chooseInstitution = (institution: Institution) => {
    setSelectedInstitution(institution)
    setSelectedProgramme(null)
    setProgrammeSearch('')
    setGoalScope('institution')
    setSelectionNotice('')
  }

  const chooseProgramme = (programme: Programme) => {
    setSelectedProgramme(programme)
    setGoalScope('programme')
    setSelectionNotice('')
  }

  const saveGoal = () => {
    if (!selectedInstitution || !goalsQ.isSuccess) return
    const kind: EducationGoalKind = goalSlot === 'primary' ? 'primary' : 'alternative'
    const priority: 1 | 2 = goalSlot === 'alternative-2' ? 2 : 1
    create.mutate({
      institution: selectedInstitution.id,
      programme: goalScope === 'programme' ? selectedProgramme?.id ?? null : null,
      kind,
      priority,
    })
  }

  const noOpenSlots = goalsQ.isSuccess && usedSlots.size >= 3

  return (
    <div className="student-page education-goals-page">
      <header className="education-goals-hero">
        <div>
          <h1>Plan education goals</h1>
          <p>Explore sourced institutions and programmes, then save routes you want to compare.</p>
        </div>
        <Link to="/grades" className="education-goals-hero__link">Back to My Progress</Link>
      </header>

      <section className="education-goals-saved" aria-labelledby="saved-education-goals-title">
        <div className="education-section-heading">
          <div>
            <h2 id="saved-education-goals-title">Your exploration routes</h2>
            <p>Keep one primary route and up to two alternatives. These are planning choices, not admission outcomes.</p>
          </div>
          <span>1 primary + up to 2 alternatives</span>
        </div>
        {goalsQ.isLoading ? (
          <LoadingSkeleton label="Loading saved education goals" rows={2} variant="list" />
        ) : goalsQ.isError ? (
          <ErrorState
            title="Saved education goals could not load"
            description="Your saved routes are unchanged. Try loading them again."
            actionLabel="Retry saved goals"
            onRetry={() => goalsQ.refetch()}
          />
        ) : (goalsQ.data ?? []).length === 0 ? (
          <EmptyState
            title="No education goals saved yet"
            description="Choose an institution or programme below to begin your exploration routes."
          />
        ) : (
          <EducationGoalList goals={goalsQ.data ?? []} usedSlots={usedSlots} />
        )}
      </section>

      <div className="education-explorer-layout">
        {selectionNotice && <p className="education-selection-notice" role="status">{selectionNotice}</p>}
        <section className="education-catalogue" aria-labelledby="institution-catalogue-title">
          <div className="education-section-heading">
            <div>
              <h2 id="institution-catalogue-title">Find an institution</h2>
              <p>Search source-dated catalogue records and choose one to explore.</p>
            </div>
          </div>
          <div className="education-filter-grid">
            <div className="student-field education-field--wide">
              <label htmlFor="institution-search">Search institutions</label>
              <input
                id="institution-search"
                className="student-field__control"
                value={institutionSearch}
                onChange={(event) => setInstitutionSearch(event.target.value)}
                placeholder="Name or catalogue code"
              />
            </div>
            <div className="student-field">
              <label htmlFor="institution-county">County</label>
              <select id="institution-county" className="student-field__control" value={county} onChange={(event) => setCounty(event.target.value)}>
                <option value="">All counties</option>
                {facetOptions.counties.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
            <div className="student-field">
              <label htmlFor="institution-framework">Framework</label>
              <select id="institution-framework" className="student-field__control" value={framework} onChange={(event) => setFramework(event.target.value)}>
                <option value="">All frameworks</option>
                {facetOptions.frameworks.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
            <div className="student-field">
              <label htmlFor="institution-cycle">Admission cycle</label>
              <select id="institution-cycle" className="student-field__control" value={cycle} onChange={(event) => setCycle(event.target.value)}>
                <option value="">All cycles</option>
                {facetOptions.cycles.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
            <div className="student-field">
              <label htmlFor="institution-verification">Verification status</label>
              <select
                id="institution-verification"
                className="student-field__control"
                value={verificationStatus}
                onChange={(event) => setVerificationStatus(event.target.value as CatalogueFilters['verification_status'] | '')}
              >
                <option value="">All statuses</option>
                {facetOptions.verificationStatuses.map((value) => (
                  <option key={value} value={value}>
                    {value === 'historical' ? 'Historical' : value === 'verified' ? 'Verified' : 'Unavailable'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {institutionsQ.isLoading ? (
            <LoadingSkeleton label="Loading institutions" rows={3} variant="list" />
          ) : institutionsQ.isError ? (
            <ErrorState
              title="Institutions could not load"
              description="Check your connection and retry the institution catalogue."
              actionLabel="Retry institutions"
              onRetry={() => institutionsQ.refetch()}
            />
          ) : (institutionsQ.data ?? []).length === 0 ? (
            <EmptyState
              title="No institutions match these filters"
              description="Try a different search, county, framework, cycle, or verification status."
            />
          ) : (
            <div className="education-catalogue-list">
              {(institutionsQ.data ?? []).map((institution) => (
                <button
                  key={institution.id}
                  type="button"
                  className={`education-catalogue-row${selectedInstitution?.id === institution.id ? ' is-selected' : ''}`}
                  onClick={() => chooseInstitution(institution)}
                  aria-pressed={selectedInstitution?.id === institution.id}
                  aria-label={`Explore ${institution.name}`}
                >
                  <span><strong>{institution.name}</strong><small>{institution.institution_type} · {institution.county}</small></span>
                  <span>{institution.verification_status === 'historical' ? 'Historical reference' : 'Catalogue reference'}</span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="education-programmes" aria-labelledby="programme-catalogue-title">
          <div className="education-section-heading">
            <div>
              <h2 id="programme-catalogue-title">Explore programmes</h2>
              <p>{selectedInstitution ? `Programmes at ${selectedInstitution.name}` : 'Choose an institution to see its programmes.'}</p>
            </div>
          </div>

          {!selectedInstitution ? (
            <div className="education-selection-prompt">Select an institution to continue.</div>
          ) : (
            <>
              <div className="education-selected-source" role="region" aria-label="Selected institution source">
                <strong>{selectedInstitution.name}</strong>
                <small>
                  {selectedInstitution.education_framework} · {selectedInstitution.admission_cycle} · Effective {displayDate(selectedInstitution.effective_date)} · Verification: {selectedInstitution.verification_status === 'historical' ? 'Historical' : selectedInstitution.verification_status === 'verified' ? 'Verified' : 'Unavailable'}
                </small>
                <a href={selectedInstitution.source_url} target="_blank" rel="noreferrer" className="education-reference-source">
                  Open institution source
                </a>
              </div>
              <div className="student-field">
                <label htmlFor="programme-search">Search programmes</label>
                <input
                  id="programme-search"
                  className="student-field__control"
                  value={programmeSearch}
                  onChange={(event) => setProgrammeSearch(event.target.value)}
                  placeholder="Programme name or code"
                />
              </div>
              {programmesQ.isLoading ? (
                <LoadingSkeleton label="Loading programmes" rows={3} variant="list" />
              ) : programmesQ.isError ? (
                <ErrorState
                  title="Programmes could not load"
                  description="The chosen institution is still selected. Retry its programme catalogue."
                  actionLabel="Retry programmes"
                  onRetry={() => programmesQ.refetch()}
                />
              ) : (programmesQ.data ?? []).length === 0 ? (
                <EmptyState
                  title="No programmes match this search"
                  description="Try a different programme name or catalogue code."
                />
              ) : (
                <div className="education-programme-list">
                  {(programmesQ.data ?? []).map((programme) => (
                    <button
                      key={programme.id}
                      type="button"
                      className={`education-programme-row${selectedProgramme?.id === programme.id ? ' is-selected' : ''}`}
                      aria-pressed={selectedProgramme?.id === programme.id}
                      aria-label={`View ${programme.name}`}
                      onClick={() => chooseProgramme(programme)}
                    >
                      <span><strong>{programme.name}</strong><small>{programme.code}</small></span>
                      <span>View details</span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}

          {selectedInstitution && (
            <form className="education-goal-form" onSubmit={(event) => { event.preventDefault(); saveGoal() }}>
              <h3>Save this route</h3>
              <div className="student-field">
                <label htmlFor="goal-scope">Goal scope</label>
                <select id="goal-scope" className="student-field__control" value={goalScope} onChange={(event) => setGoalScope(event.target.value as 'institution' | 'programme')}>
                  <option value="institution">Institution only</option>
                  <option value="programme" disabled={!selectedProgramme}>Selected programme</option>
                </select>
              </div>
              <div className="student-field">
                <label htmlFor="new-goal-slot">Goal slot</label>
                <select id="new-goal-slot" className="student-field__control" value={goalSlot} onChange={(event) => setGoalSlot(event.target.value)} disabled={!goalsQ.isSuccess || noOpenSlots}>
                  <option value="primary" disabled={usedSlots.has('primary')}>Primary{usedSlots.has('primary') ? ' (already used)' : ''}</option>
                  <option value="alternative-1" disabled={usedSlots.has('alternative-1')}>Alternative 1{usedSlots.has('alternative-1') ? ' (already used)' : ''}</option>
                  <option value="alternative-2" disabled={usedSlots.has('alternative-2')}>Alternative 2{usedSlots.has('alternative-2') ? ' (already used)' : ''}</option>
                </select>
              </div>
              {!goalsQ.isSuccess && <p className="education-slot-note">Saved goals must load before you can save another route.</p>}
              {noOpenSlots && <p className="education-slot-note">All three education-goal slots are filled. Update or remove a saved route first.</p>}
              <button
                type="submit"
                className="student-action"
                disabled={!goalsQ.isSuccess || create.isPending || noOpenSlots || (goalScope === 'programme' && !selectedProgramme)}
              >
                {create.isPending ? 'Saving…' : 'Save education goal'}
              </button>
            </form>
          )}
        </section>
      </div>

      {selectedProgramme && (
        <section className="education-detail-shell" aria-live="polite">
          {detailQ.isLoading ? (
            <LoadingSkeleton label="Loading programme details" rows={5} variant="page" />
          ) : detailQ.isError ? (
            <ErrorState
              title="Programme details could not load"
              description="The selected programme is unchanged. Try loading its sourced detail again."
              actionLabel="Retry programme details"
              onRetry={() => detailQ.refetch()}
            />
          ) : detailQ.data ? <ProgrammeReferenceDetail programme={detailQ.data} /> : null}
        </section>
      )}

      <p className="education-goals-disclaimer">
        Education goals are exploratory. Confirm current requirements and decisions through official services and your counsellor.
      </p>
    </div>
  )
}
