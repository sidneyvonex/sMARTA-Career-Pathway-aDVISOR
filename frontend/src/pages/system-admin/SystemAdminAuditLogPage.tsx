import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { systemAdminApi, type AuditEntry } from '../../api/systemAdmin'
import EmptyState from '../../components/common/dashboard/EmptyState'
import DetailDrawer from '../../components/common/management/DetailDrawer'
import ManagementPage from '../../components/common/management/ManagementPage'
import ManagementTable from '../../components/common/management/ManagementTable'
import ManagementToolbar from '../../components/common/management/ManagementToolbar'
import type { ManagementColumn } from '../../components/common/management/types'
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
  counselor_added: 'Counsellor added',
  counselor_removed: 'Counsellor removed',
  counselor_assigned: 'Counsellor assigned',
  school_membership_approved: 'School link approved',
  school_membership_rejected: 'School link rejected',
  grade_verified: 'Grade verified',
  grade_verification_removed: 'Grade verification removed',
  parent_link_approved: 'Parent link approved',
  parent_link_revoked: 'Parent link revoked',
  provisional_combination_changed: 'Provisional combination changed',
  plan_review_status_changed: 'Plan review status changed',
  report_downloaded: 'Report downloaded',
  framework_combination_status_changed: 'Framework combination changed',
  school_offerings_changed: 'School offerings changed',
}

const ACTION_OPTIONS = [
  { value: '', label: 'All events' },
  ...Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label })),
]

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString('en-KE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatLabel(value: string): string {
  const words = value.replace(/_/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function actionLabel(entry: AuditEntry): string {
  return ACTION_LABELS[entry.action] ?? formatLabel(entry.action)
}

function targetLabel(entry: AuditEntry): string {
  return `${entry.target_type.replace(/_/g, ' ')} #${entry.target_id}`
}

function formatDetailValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Not recorded'
  if (Array.isArray(value)) return value.map(formatDetailValue).join(', ')
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, nestedValue]) => `${formatLabel(key)}: ${formatDetailValue(nestedValue)}`)
      .join(' · ')
  }
  return String(value)
}

function detailsSummary(details: Record<string, unknown>): string {
  const values = Object.values(details)
    .map(formatDetailValue)
    .filter(value => value !== 'Not recorded')
    .slice(0, 2)

  return values.length > 0 ? values.join(' · ') : 'No additional metadata'
}

export default function SystemAdminAuditLogPage() {
  const [action, setAction] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const [detailEntry, setDetailEntry] = useState<AuditEntry | null>(null)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['system-admin', 'audit-logs', { action, dateFrom, dateTo, page }],
    queryFn: () => systemAdminApi.getAuditLogs({
      ...(action && { action }),
      ...(dateFrom && { date_from: dateFrom }),
      ...(dateTo && { date_to: dateTo }),
      page,
    }).then(response => response.data.data),
  })

  useEffect(() => {
    if (isError) toast.error('Failed to load audit logs.')
  }, [isError])

  const entries = data?.results ?? []
  const total = data?.total ?? 0
  const pageSize = data?.page_size ?? 20
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const columns: ManagementColumn<AuditEntry>[] = [
    {
      key: 'time',
      label: 'Time',
      priority: 'essential',
      render: entry => <time dateTime={entry.created_at}>{formatTimestamp(entry.created_at)}</time>,
    },
    {
      key: 'actor',
      label: 'Actor',
      priority: 'identity',
      render: entry => (
        <div className="admin-person">
          <strong>{entry.actor_name ?? 'System event'}</strong>
          <span>{entry.actor_email ?? 'No account email'}</span>
        </div>
      ),
    },
    {
      key: 'event',
      label: 'Event',
      priority: 'essential',
      render: entry => <span className="sysadmin-badge sysadmin-badge--active">{actionLabel(entry)}</span>,
    },
    {
      key: 'target',
      label: 'Affected record',
      priority: 'secondary',
      render: targetLabel,
    },
    {
      key: 'summary',
      label: 'Summary',
      priority: 'secondary',
      render: entry => <span className="sysadmin-audit-summary">{detailsSummary(entry.details)}</span>,
    },
  ]

  const toolbar = (
    <ManagementToolbar
      className="sysadmin-audit-toolbar"
      resultCount={`${total} ${total === 1 ? 'entry' : 'entries'}`}
      search={(
        <label htmlFor="audit-event">
          <span>Event</span>
          <select id="audit-event" value={action} onChange={event => { setAction(event.target.value); setPage(1) }}>
            {ACTION_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
      )}
      filters={(
        <>
          <label htmlFor="audit-date-from">
            <span>From</span>
            <input id="audit-date-from" type="date" value={dateFrom} onChange={event => { setDateFrom(event.target.value); setPage(1) }} />
          </label>
          <label htmlFor="audit-date-to">
            <span>To</span>
            <input id="audit-date-to" type="date" value={dateTo} onChange={event => { setDateTo(event.target.value); setPage(1) }} />
          </label>
        </>
      )}
    />
  )

  return (
    <>
      <div className="sysadmin-audit-page">
        <ManagementPage
          eyebrow="Operational history"
          title="Audit log"
          description="Review who changed platform data, when it happened, and which record was affected. Full metadata stays in the details drawer."
          toolbar={toolbar}
          loading={isLoading}
          error={isError ? { title: 'Audit log could not load', description: 'No audit data was changed. Check your connection and try again.' } : undefined}
          onRetry={() => refetch()}
        >
          <ManagementTable
            ariaLabel="Audit log entries"
            records={entries}
            columns={columns}
            getKey={entry => entry.id}
            getRecordLabel={entry => `${actionLabel(entry)} ${entry.id}`}
            getPrimaryAction={entry => ({
              id: 'view-details',
              label: `View details for ${actionLabel(entry)}`,
              shortLabel: 'Details',
              onSelect: () => setDetailEntry(entry),
            })}
            getSecondaryActions={() => []}
            empty={<EmptyState title="No audit entries found" description="Try changing the event or date filters." />}
          />

          {totalPages > 1 && (
            <nav className="sysadmin-pagination" aria-label="Audit log pages">
              <button type="button" className="btn-ghost" onClick={() => setPage(value => Math.max(1, value - 1))} disabled={page <= 1}>Previous</button>
              <span aria-live="polite">Page {page} of {totalPages}</span>
              <button type="button" className="btn-ghost" onClick={() => setPage(value => Math.min(totalPages, value + 1))} disabled={page >= totalPages}>Next</button>
            </nav>
          )}
        </ManagementPage>
      </div>

      <DetailDrawer
        open={detailEntry !== null}
        title={detailEntry ? `${actionLabel(detailEntry)} details` : 'Audit event details'}
        onClose={() => setDetailEntry(null)}
      >
        {detailEntry && (
          <dl className="sysadmin-detail-list">
            <div><dt>Actor</dt><dd>{detailEntry.actor_name ?? 'System event'}</dd></div>
            <div><dt>Actor email</dt><dd>{detailEntry.actor_email ?? 'No account email'}</dd></div>
            <div><dt>Event</dt><dd>{actionLabel(detailEntry)}</dd></div>
            <div><dt>Affected record</dt><dd>{targetLabel(detailEntry)}</dd></div>
            <div><dt>IP address</dt><dd>{detailEntry.ip_address ?? 'Not recorded'}</dd></div>
            <div><dt>Timestamp</dt><dd>{formatTimestamp(detailEntry.created_at)}</dd></div>
            {Object.entries(detailEntry.details).map(([key, value]) => (
              <div key={key}><dt>{formatLabel(key)}</dt><dd>{formatDetailValue(value)}</dd></div>
            ))}
          </dl>
        )}
      </DetailDrawer>
    </>
  )
}
