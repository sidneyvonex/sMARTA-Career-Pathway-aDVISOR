import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import toast from 'react-hot-toast'

import { devMailApi } from '../api/devMail'
import '../styles/letters.css'

// Used for splitting the body into text and URL parts.
const URL_SPLITTER = /(https?:\/\/[^\s]+)/g
// Stateless test — no `g` flag — safe for repeated calls in .map().
const URL_TEST = /https?:\/\/[^\s]+/

function LinkifiedBody({ body }: { body: string }) {
  const parts = body.split(URL_SPLITTER)
  return (
    <pre className="letters-body">
      {parts.map((part, i) =>
        URL_TEST.test(part) ? (
          <a key={i} href={part} target="_blank" rel="noreferrer">
            {part}
          </a>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </pre>
  )
}

export default function LettersPage() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const listQuery = useQuery({
    queryKey: ['dev-letters'],
    queryFn: async () => (await devMailApi.list()).data.data,
  })

  const detailQuery = useQuery({
    queryKey: ['dev-letter', selectedId],
    queryFn: async () => (await devMailApi.get(selectedId as number)).data.data,
    enabled: selectedId !== null,
  })

  const clearMutation = useMutation({
    mutationFn: () => devMailApi.clear(),
    onSuccess: () => {
      toast.success('Inbox cleared.')
      setSelectedId(null)
      queryClient.invalidateQueries({ queryKey: ['dev-letters'] })
    },
    onError: () => toast.error('Could not clear the inbox.'),
  })

  const letters = listQuery.data ?? []

  return (
    <main className="letters-page">
      <header className="letters-header">
        <h1>Dev Mailbox</h1>
        <span className="letters-dev-chip" aria-label="Development tool only">DEV</span>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => clearMutation.mutate()}
          disabled={clearMutation.isPending || letters.length === 0}
        >
          Clear inbox
        </button>
      </header>

      <div className="letters-layout">
        <ul className="letters-list">
          {letters.length === 0 && (
            <li className="letters-empty">No emails captured yet</li>
          )}
          {letters.map((letter) => (
            <li key={letter.id}>
              <button
                type="button"
                className={selectedId === letter.id ? 'letters-list-item--active' : undefined}
                onClick={() => setSelectedId(letter.id)}
              >
                <span className="letters-subject">{letter.subject}</span>
                <span className="letters-to">{letter.to_email}</span>
                <time dateTime={letter.created_at}>
                  {new Date(letter.created_at).toLocaleString()}
                </time>
              </button>
            </li>
          ))}
        </ul>

        <section className="letters-detail">
          {selectedId === null && (
            <p className="letters-detail-hint">Select an email to read it.</p>
          )}
          {detailQuery.data && (
            <>
              <h2>{detailQuery.data.subject}</h2>
              <p>To: {detailQuery.data.to_email}</p>
              <p>From: {detailQuery.data.from_email}</p>
              <LinkifiedBody body={detailQuery.data.body} />
            </>
          )}
        </section>
      </div>
    </main>
  )
}
