interface Props {
  activeFilter: string
  onFilterChange: (filter: string) => void
  searchQuery: string
  onSearchChange: (query: string) => void
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
