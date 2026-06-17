import { useState, useEffect } from 'react'

interface Props {
  onSubmit: (body: string) => void
  onCancel?: () => void
  initialBody?: string
  isPending: boolean
}

const MAX_LENGTH = 2000

export default function NoteForm({ onSubmit, onCancel, initialBody, isPending }: Props) {
  const [body, setBody] = useState(initialBody ?? '')
  const isEditing = initialBody !== undefined

  useEffect(() => {
    setBody(initialBody ?? '')
  }, [initialBody])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = body.trim()
    if (!trimmed) return
    onSubmit(trimmed)
    if (!isEditing) setBody('')
  }

  return (
    <form className="note-form" onSubmit={handleSubmit}>
      <label htmlFor="note-body" className="note-form__label">
        {isEditing ? 'Edit note' : 'Add a note'}
      </label>
      <textarea
        id="note-body"
        className="note-form__textarea"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        maxLength={MAX_LENGTH}
        placeholder="Write a counseling note..."
        rows={3}
        disabled={isPending}
      />
      <div className="note-form__footer">
        <span className="note-form__counter">
          {body.length}/{MAX_LENGTH}
        </span>
        <div className="note-form__actions">
          {isEditing && onCancel && (
            <button
              type="button"
              className="btn-ghost"
              onClick={onCancel}
              disabled={isPending}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className="btn-primary"
            disabled={isPending || !body.trim()}
          >
            {isPending ? 'Saving...' : isEditing ? 'Update' : 'Save'}
          </button>
        </div>
      </div>
    </form>
  )
}
