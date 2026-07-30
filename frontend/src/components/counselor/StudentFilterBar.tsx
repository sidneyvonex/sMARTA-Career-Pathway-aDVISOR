interface Props {
  activeFilter: string
  onFilterChange: (filter: string) => void
  searchQuery: string
  onSearchChange: (query: string) => void
  reasonFilter: string
  onReasonChange: (reason: string) => void
}

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'needs_attention', label: 'Needs attention' },
  { key: 'assessed', label: 'Assessed' },
  { key: 'new', label: 'New' },
]

export default function StudentFilterBar({
  activeFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
  reasonFilter,
  onReasonChange,
}: Props) {
  return (
    <div className="filter-bar">
      <div className="filter-bar__chips">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            className={`filter-chip${activeFilter === f.key ? ' filter-chip--active' : ''}`}
            onClick={() => onFilterChange(f.key)}
            aria-pressed={activeFilter === f.key}
          >
            {f.label}
          </button>
        ))}
      </div>
      <select
        className="filter-select"
        value={reasonFilter}
        onChange={(event) => onReasonChange(event.target.value)}
        aria-label="Filter by attention reason"
      >
        <option value="all">All attention reasons</option>
        <option value="learner_requested_review">Review requested</option>
        <option value="follow_up_overdue">Follow-up overdue</option>
        <option value="combination_unavailable_at_school">Combination unavailable</option>
        <option value="academic_evidence_missing">Academic evidence incomplete</option>
        <option value="assessment_missing">Interest assessment missing</option>
        <option value="no_saved_combination">No saved combination</option>
        <option value="no_plan">No learner plan</option>
      </select>
      <input
        type="search"
        className="search-input"
        placeholder="Search by name..."
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        aria-label="Search students by name"
      />
    </div>
  )
}
