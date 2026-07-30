import { FormEvent, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { studentsApi, type ParentAccess } from '../api/students'
import ErrorState from '../components/common/dashboard/ErrorState'
import '../styles/access.css'

const accessKey = ['student', 'parent-access'] as const

export default function ParentAccessPage() {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const accessQuery = useQuery({
    queryKey: accessKey,
    queryFn: () => studentsApi.getParentAccess(),
  })
  const inviteMutation = useMutation({
    mutationFn: () => authApi.inviteParent(email.trim()),
    onSuccess: () => {
      setEmail('')
      toast.success('Invitation sent.')
    },
    onError: () => toast.error('Could not send that invitation.'),
  })
  const approveMutation = useMutation({
    mutationFn: (linkId: number) => studentsApi.approveParentAccess(linkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accessKey })
      toast.success('Parent access approved.')
    },
    onError: () => toast.error('Could not approve this request.'),
  })
  const revokeMutation = useMutation({
    mutationFn: (linkId: number) => studentsApi.revokeParentAccess(linkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accessKey })
      toast.success('Parent access revoked.')
    },
    onError: () => toast.error('Could not revoke this access.'),
  })

  if (accessQuery.isLoading) {
    return <div className="access-loading" aria-label="Loading parent access"><div /><div /></div>
  }
  if (accessQuery.isError) {
    return (
      <ErrorState
        title="Parent access could not load"
        description="Check your connection and try loading your access requests again."
        onRetry={() => accessQuery.refetch()}
      />
    )
  }

  const links = accessQuery.data?.data.data ?? []
  const pending = links.filter((link) => (
    link.status === 'pending_learner' || link.status === 'invited'
  ))
  const active = links.filter((link) => link.status === 'active')
  const revoked = links.filter((link) => link.status === 'revoked')

  const submitInvite = (event: FormEvent) => {
    event.preventDefault()
    if (email.trim()) inviteMutation.mutate()
  }

  return (
    <div className="access-page">
      <header className="access-header">
        <span>Privacy and support</span>
        <h1>Control who can view your progress</h1>
        <p>Parent access begins only after you approve it. You can revoke active access at any time.</p>
      </header>

      <aside className="access-notice" role="note">
        <strong>Pilot identity notice</strong>
        <p>
          Smarta Shauri records the relationship a person claims. Legal guardian identity is not independently verified in this pilot. Approve only someone you know and trust.
        </p>
      </aside>

      <section className="access-invite" aria-labelledby="invite-supporter-title">
        <div>
          <span>Invite</span>
          <h2 id="invite-supporter-title">Invite a parent or guardian</h2>
          <p>They will create an account and then appear here for your approval.</p>
        </div>
        <form onSubmit={submitInvite}>
          <label htmlFor="parent-email">Parent or guardian email</label>
          <div>
            <input
              id="parent-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="supporter@example.com"
              required
            />
            <button type="submit" disabled={inviteMutation.isPending || !email.trim()}>
              {inviteMutation.isPending ? 'Sending...' : 'Send invitation'}
            </button>
          </div>
        </form>
      </section>

      <AccessSection
        title="Requests awaiting your decision"
        description="Review the claimed relationship before granting access."
        empty="No parent access requests are waiting."
        links={pending}
      >
        {(link) => (
          <div className="access-actions">
            <button
              type="button"
              disabled={approveMutation.isPending || revokeMutation.isPending}
              onClick={() => approveMutation.mutate(link.id)}
            >
              Approve access
            </button>
            <button
              type="button"
              className="access-button--danger"
              disabled={approveMutation.isPending || revokeMutation.isPending}
              onClick={() => revokeMutation.mutate(link.id)}
            >
              Decline
            </button>
          </div>
        )}
      </AccessSection>

      <AccessSection
        title="People with access"
        description="Active supporters can view approved learner information and reports."
        empty="No parent or guardian currently has access."
        links={active}
      >
        {(link) => (
          <button
            type="button"
            className="access-button--danger"
            disabled={revokeMutation.isPending}
            onClick={() => revokeMutation.mutate(link.id)}
          >
            Revoke access
          </button>
        )}
      </AccessSection>

      {revoked.length > 0 && (
        <AccessSection
          title="Revoked access"
          description="These accounts can no longer view your information."
          empty=""
          links={revoked}
        />
      )}
    </div>
  )
}

function AccessSection({
  title,
  description,
  empty,
  links,
  children,
}: {
  title: string
  description: string
  empty: string
  links: ParentAccess[]
  children?: (link: ParentAccess) => React.ReactNode
}) {
  return (
    <section className="access-section">
      <header>
        <h2>{title}</h2>
        <p>{description}</p>
      </header>
      {links.length ? (
        <div className="access-list">
          {links.map((link) => (
            <article key={link.id} className="access-card">
              <div className="access-avatar" aria-hidden="true">
                {initials(link.parent_name)}
              </div>
              <div>
                <h3>{link.parent_name}</h3>
                <p>{link.parent_email}</p>
                <span>Claims to be: {link.relationship_label}</span>
              </div>
              {children?.(link)}
            </article>
          ))}
        </div>
      ) : (
        <p className="access-empty">{empty}</p>
      )}
    </section>
  )
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}
