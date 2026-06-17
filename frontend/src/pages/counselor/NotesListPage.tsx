import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import { counselorApi } from '../../api/counselor'
import type { CounselorNote } from '../../api/counselor'
import NoteCard from '../../components/counselor/NoteCard'
import NoteForm from '../../components/counselor/NoteForm'
import { initials } from '../../lib/format'
import '../../styles/counselor.css'

export default function NotesListPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['counselor', 'notes'],
    queryFn: async () => {
      const res = await counselorApi.getNotes()
      return res.data.data
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ noteId, body }: { noteId: number; body: string }) =>
      counselorApi.updateNote(noteId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
      toast.success('Note updated.')
      setEditingNoteId(null)
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Something went wrong. Please try again.'
      toast.error(msg)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (noteId: number) => counselorApi.deleteNote(noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
      toast.success('Note removed.')
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      const msg = typeof message === 'string' ? message : 'Something went wrong. Please try again.'
      toast.error(msg)
    },
  })

  useEffect(() => {
    if (isError) {
      toast.error('Failed to load notes. Please try again.')
    }
  }, [isError])

  const notes = data ?? []
  const query = search.toLowerCase().trim()
  const filtered = query
    ? notes.filter(
        (n) =>
          n.student_name.toLowerCase().includes(query) ||
          n.body.toLowerCase().includes(query)
      )
    : notes

  function handleEdit(note: CounselorNote) {
    setEditingNoteId(note.id)
  }

  function handleDelete(noteId: number) {
    deleteMutation.mutate(noteId)
  }

  function handleUpdate(noteId: number, body: string) {
    updateMutation.mutate({ noteId, body })
  }

  function handleCancelEdit() {
    setEditingNoteId(null)
  }

  return (
    <div className="counselor-page notes-list-page">
      <div className="counselor-page__header">
        <div>
          <h1 className="counselor-page__title">My Notes</h1>
          {!isLoading && (
            <span className="counselor-page__count">
              {notes.length} {notes.length === 1 ? 'note' : 'notes'} total
            </span>
          )}
        </div>
        <input
          type="search"
          className="search-input"
          placeholder="Search notes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search notes"
        />
      </div>

      {isLoading && (
        <div className="notes-list" role="status" aria-label="Loading notes">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="note-card skeleton-note">
              <div className="skeleton-bar skeleton-bar--medium skeleton-pulse" />
              <div className="skeleton-bar skeleton-bar--long skeleton-pulse" style={{ marginTop: 'var(--space-2)' }} />
              <div className="skeleton-bar skeleton-bar--short skeleton-pulse" style={{ marginTop: 'var(--space-3)' }} />
            </div>
          ))}
        </div>
      )}

      {!isLoading && filtered.length === 0 && (
        <div className="notes-list__empty">
          {query
            ? `No notes matching "${search}".`
            : 'No notes yet. Visit a student’s profile to add one.'}
        </div>
      )}

      {!isLoading && filtered.length > 0 && (
        <div className="notes-list">
          {filtered.map((note) => (
            <div key={note.id} className="notes-list__item">
              <div className="notes-list__student-header">
                <div className="student-cell__avatar">
                  {initials(
                    note.student_name.split(' ')[0] ?? '',
                    note.student_name.split(' ').slice(1).join(' ') ?? ''
                  )}
                </div>
                <Link
                  to={`/counselor/students/${note.student}`}
                  className="note-card__student-link"
                >
                  {note.student_name}
                </Link>
              </div>

              {editingNoteId === note.id ? (
                <NoteForm
                  initialBody={note.body}
                  isPending={updateMutation.isPending}
                  onSubmit={(body) => handleUpdate(note.id, body)}
                  onCancel={handleCancelEdit}
                />
              ) : (
                <NoteCard
                  note={note}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
