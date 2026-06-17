import { formatRelativeTime } from '../../lib/format'
import type { CounselorNote } from '../../api/counselor'

interface Props {
  note: CounselorNote
  onEdit: (note: CounselorNote) => void
  onDelete: (noteId: number) => void
}

export default function NoteCard({ note, onEdit, onDelete }: Props) {
  return (
    <div className="note-card">
      <p className="note-card__body">{note.body}</p>

      <div className="note-card__footer">
        <span className="note-card__time">
          {formatRelativeTime(note.updated_at)}
        </span>

        <div className="note-card__actions">
          <button
            type="button"
            className="note-card__action"
            onClick={() => onEdit(note)}
            aria-label="Edit note"
          >
            Edit
          </button>
          <button
            type="button"
            className="note-card__action note-card__action--danger"
            onClick={() => {
              if (window.confirm('Delete this note? This cannot be undone.')) {
                onDelete(note.id)
              }
            }}
            aria-label="Delete note"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
