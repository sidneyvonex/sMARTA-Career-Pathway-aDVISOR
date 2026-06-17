import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { counselorApi, type CounselorNote } from '../../api/counselor'
import type { RIASECDimension } from '../../api/assessment'
import StudentDetailHeader from '../../components/counselor/StudentDetailHeader'
import CounselorGradesTable from '../../components/counselor/CounselorGradesTable'
import NoteCard from '../../components/counselor/NoteCard'
import NoteForm from '../../components/counselor/NoteForm'
import ScoreBars from '../../components/assessment/ScoreBars'
import RecommendationCards from '../../components/assessment/RecommendationCards'
import '../../styles/counselor.css'

export default function StudentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const studentId = Number(id)
  const queryClient = useQueryClient()

  const [editingNote, setEditingNote] = useState<CounselorNote | null>(null)

  const studentQuery = useQuery({
    queryKey: ['counselor', 'student', studentId],
    queryFn: () => counselorApi.getStudent(studentId).then((r) => r.data.data),
    enabled: !isNaN(studentId),
  })

  const notesQuery = useQuery({
    queryKey: ['counselor', 'notes'],
    queryFn: () => counselorApi.getNotes().then((r) => r.data.data),
  })

  const studentNotes = (notesQuery.data ?? []).filter(
    (n) => n.student === studentId,
  )

  const createNote = useMutation({
    mutationFn: (body: string) => counselorApi.createNote(studentId, body),
    onSuccess: () => {
      const firstName = studentQuery.data?.student.first_name ?? 'student'
      toast.success(`Note saved for ${firstName}.`)
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'student', studentId] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Something went wrong. Please try again.')
    },
  })

  const updateNote = useMutation({
    mutationFn: ({ noteId, body }: { noteId: number; body: string }) =>
      counselorApi.updateNote(noteId, body),
    onSuccess: () => {
      toast.success('Note updated.')
      setEditingNote(null)
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Something went wrong. Please try again.')
    },
  })

  const deleteNote = useMutation({
    mutationFn: (noteId: number) => counselorApi.deleteNote(noteId),
    onSuccess: () => {
      toast.success('Note removed.')
      queryClient.invalidateQueries({ queryKey: ['counselor', 'notes'] })
      queryClient.invalidateQueries({ queryKey: ['counselor', 'student', studentId] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.message
      toast.error(typeof message === 'string' ? message : 'Something went wrong. Please try again.')
    },
  })

  if (studentQuery.isLoading) {
    return (
      <div className="counselor-page">
        <div className="student-detail__loading">
          <div className="skeleton-bar skeleton-bar--long" />
          <div className="skeleton-bar skeleton-bar--medium" />
          <div className="skeleton-bar skeleton-bar--short" />
        </div>
      </div>
    )
  }

  if (studentQuery.isError || !studentQuery.data) {
    return (
      <div className="counselor-page">
        <div className="table-empty">
          Could not load student details.{' '}
          <Link to="/counselor/students" className="view-link">
            Back to students
          </Link>
        </div>
      </div>
    )
  }

  const { student, riasec_result, grades } = studentQuery.data

  return (
    <div className="counselor-page">
      <div className="student-detail__back">
        <Link to="/counselor/students" className="view-link">
          &larr; Back to students
        </Link>
      </div>

      <div className="student-detail">
        {/* Left column */}
        <div className="student-detail__main">
          <StudentDetailHeader student={student} />

          {riasec_result && (
            <section className="student-detail__section">
              <h2 className="student-detail__section-title">RIASEC Assessment</h2>
              <ScoreBars
                scores={riasec_result.scores as Record<RIASECDimension, number>}
              />
              <RecommendationCards
                recommendations={riasec_result.recommendations}
                hollandCode={riasec_result.holland_code}
              />
            </section>
          )}

          <section className="student-detail__section">
            <h2 className="student-detail__section-title">Grades</h2>
            <CounselorGradesTable grades={grades} studentName={student.first_name} />
          </section>
        </div>

        {/* Right column */}
        <div className="student-detail__sidebar">
          <div className="quick-info-card">
            <h3 className="quick-info-card__title">Quick Info</h3>
            <dl className="quick-info-card__list">
              <div className="quick-info-card__item">
                <dt>Email</dt>
                <dd>{student.email}</dd>
              </div>
              <div className="quick-info-card__item">
                <dt>County</dt>
                <dd>{student.county ?? 'Not set'}</dd>
              </div>
              <div className="quick-info-card__item">
                <dt>School</dt>
                <dd>{student.school ?? 'Not set'}</dd>
              </div>
              {student.career_interests && (
                <div className="quick-info-card__item">
                  <dt>Career interests</dt>
                  <dd>{student.career_interests}</dd>
                </div>
              )}
              <div className="quick-info-card__item">
                <dt>Joined</dt>
                <dd>
                  {new Date(student.created_at).toLocaleDateString('en-KE', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </dd>
              </div>
            </dl>
          </div>

          <div className="notes-section">
            <h3 className="notes-section__title">
              Counselor Notes
              {studentNotes.length > 0 && (
                <span className="notes-section__count">{studentNotes.length}</span>
              )}
            </h3>

            {editingNote ? (
              <NoteForm
                initialBody={editingNote.body}
                isPending={updateNote.isPending}
                onSubmit={(body) =>
                  updateNote.mutate({ noteId: editingNote.id, body })
                }
                onCancel={() => setEditingNote(null)}
              />
            ) : (
              <NoteForm
                isPending={createNote.isPending}
                onSubmit={(body) => createNote.mutate(body)}
              />
            )}

            {notesQuery.isLoading ? (
              <div className="student-detail__loading">
                <div className="skeleton-bar skeleton-bar--long" />
                <div className="skeleton-bar skeleton-bar--medium" />
              </div>
            ) : studentNotes.length === 0 ? (
              <p className="notes-section__empty">
                No notes yet. Add your first note above.
              </p>
            ) : (
              <div className="notes-section__list">
                {studentNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    onEdit={setEditingNote}
                    onDelete={(noteId) => deleteNote.mutate(noteId)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
