import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { systemAdminApi } from '../../api/systemAdmin'
import '../../styles/system-admin.css'

const ACTION_LABELS: Record<string, string> = {
  user_registered: 'User registered',
  email_verified: 'Email verified',
  password_reset: 'Password reset',
  account_deactivated: 'Account deactivated',
  account_activated: 'Account activated',
  invite_sent: 'Invite sent',
  invite_accepted: 'Invite accepted',
  school_created: 'School created',
  school_edited: 'School edited',
  school_deactivated: 'School deactivated',
  school_activated: 'School activated',
  counselor_added: 'Counselor added',
  counselor_removed: 'Counselor removed',
  counselor_assigned: 'Counselor assigned',
}

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  ...Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label })),
]

function formatTimestamp(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleString('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncateJson(details: Record<string, unknown>, maxLen = 60): string {
  const str = JSON.stringify(details)
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen) + '…'
}

export default function SystemAdminAuditLogPage() {
  // Filter state
  const [action, setAction] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)

  // Expanded details rows
  const [expandedId, setExpandedId] = useState<number | null>(null)

  // Audit logs query
  const { data, isLoading, isError } = useQuery({
    queryKey: ['system-admin', 'audit-logs', { action, dateFrom, dateTo, page }],
    queryFn: () =>
      systemAdminApi
        .getAuditLogs({
          ...(action && { action }),
          ...(dateFrom && { date_from: dateFrom }),
          ...(dateTo && { date_to: dateTo }),
          page,
        })
        .then(r => r.data.data),
  })

  useEffect(() => {
    if (isError) toast.error('Failed to load audit logs.')
  }, [isError])

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="sysadmin-page">
        <div className="skeleton" style={{ height: 40, width: '60%', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-5)' }} />
        <div className="skeleton" style={{ height: 44, width: '100%', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)' }} />
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="skeleton" style={{ height: 48, width: '100%', marginBottom: 'var(--space-2)', borderRadius: 'var(--radius-sm)' }} />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="sysadmin-page">
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          Something went wrong loading audit logs. Please try again.
        </p>
      </div>
    )
  }

  const entries = data?.results ?? []
  const total = data?.total ?? 0
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="sysadmin-page">
      {/* Header */}
      <div className="sysadmin-page__header">
        <h1 className="sysadmin-dashboard__title">Audit Log</h1>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          {total} entr{total !== 1 ? 'ies' : 'y'} total
        </span>
      </div>

      {/* Filters */}
      <div className="sysadmin-filters">
        <label htmlFor="filter-action" className="sr-only">Filter by action</label>
        <select
          id="filter-action"
          value={action}
          onChange={e => { setAction(e.target.value); setPage(1) }}
        >
          {ACTION_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <label htmlFor="filter-date-from" className="sr-only">Date from</label>
        <input
          id="filter-date-from"
          type="date"
          value={dateFrom}
          onChange={e => { setDateFrom(e.target.value); setPage(1) }}
          aria-label="Date from"
        />

        <label htmlFor="filter-date-to" className="sr-only">Date to</label>
        <input
          id="filter-date-to"
          type="date"
          value={dateTo}
          onChange={e => { setDateTo(e.target.value); setPage(1) }}
          aria-label="Date to"
        />
      </div>

      {/* Table */}
      {entries.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center', padding: 'var(--space-8)' }}>
          No audit log entries found.
        </p>
      ) : (
        <table className="sysadmin-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Target</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(entry => {
              const isExpanded = expandedId === entry.id
              const detailsStr = JSON.stringify(entry.details, null, 2)
              const hasDetails = Object.keys(entry.details).length > 0

              return (
                <tr key={entry.id}>
                  <td style={{ whiteSpace: 'nowrap' }}>{formatTimestamp(entry.created_at)}</td>
                  <td>{entry.actor_name ?? entry.actor_email ?? '—'}</td>
                  <td>
                    <span className="sysadmin-badge sysadmin-badge--active">
                      {ACTION_LABELS[entry.action] ?? entry.action}
                    </span>
                  </td>
                  <td>{entry.target_type} #{entry.target_id}</td>
                  <td>
                    {hasDetails ? (
                      <button
                        className="sysadmin-details-toggle"
                        onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                        aria-expanded={isExpanded}
                        aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
                      >
                        {isExpanded ? detailsStr : truncateJson(entry.details)}
                      </button>
                    ) : (
                      <span style={{ color: 'var(--color-text-secondary)' }}>—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="sysadmin-pagination">
          <button
            className="sysadmin-action-btn"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Previous
          </button>
          <span>Page {page} of {totalPages}</span>
          <button
            className="sysadmin-action-btn"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
