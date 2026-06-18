import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { parentApi, ChildDetail } from '../../api/parent'
import { initials } from '../../lib/format'
import '../../styles/parent.css'

const DIMENSION_LABELS: Record<string, string> = {
  R: 'Realistic',
  I: 'Investigative',
  A: 'Artistic',
  S: 'Social',
  E: 'Enterprising',
  C: 'Conventional',
}

export default function ChildDetailPage() {
  const { id } = useParams<{ id: string }>()
  const studentId = Number(id)

  const detailQ = useQuery({
    queryKey: ['parent-child-detail', studentId],
    queryFn: () => parentApi.getChildDetail(studentId).then((r) => r.data.data),
    enabled: !Number.isNaN(studentId),
  })

  useEffect(() => {
    if (detailQ.isError) {
      toast.error("Couldn't load your child's profile. Please try again.")
    }
  }, [detailQ.isError])

  if (detailQ.isLoading) {
    return (
      <div className="child-detail">
        <div className="skeleton" style={{ height: 100, borderRadius: 13 }} />
        <div className="skeleton" style={{ height: 200, borderRadius: 13 }} />
        <div className="skeleton" style={{ height: 200, borderRadius: 13 }} />
      </div>
    )
  }

  if (detailQ.isError) {
    return (
      <div className="child-detail">
        <Link to="/" className="child-detail__back" aria-label="Back to dashboard">← Back</Link>
        <div className="child-detail__section" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Couldn't load profile. Please try again.
          </p>
        </div>
      </div>
    )
  }

  const data: ChildDetail = detailQ.data!
  const { profile, subjects, assessment, counselor, latest_note } = data
  const maxScore = assessment ? Math.max(...Object.values(assessment.scores)) : 0

  return (
    <div className="child-detail">
      <Link to="/" className="child-detail__back" aria-label="Back to dashboard">← Back to dashboard</Link>

      {/* Header */}
      <div className="child-detail__header" role="region" aria-label="Child profile header">
        <div className="child-detail__avatar" aria-hidden="true">
          {initials(profile.first_name, profile.last_name)}
        </div>
        <div>
          <div className="child-detail__name">{profile.first_name} {profile.last_name}</div>
          <div className="child-detail__meta">
            Grade {profile.grade} · {profile.county ?? 'No county'} · {profile.mode === 'school_linked' ? 'School-linked' : 'Self-guided'}
          </div>
          {profile.bio && (
            <div className="child-detail__meta" style={{ marginTop: 'var(--space-2)' }}>{profile.bio}</div>
          )}
        </div>
      </div>

      {/* Career Personality */}
      <div className="child-detail__section">
        <h2 className="child-detail__section-title">{profile.first_name}'s career personality</h2>
        {assessment ? (
          <>
            <div style={{ marginBottom: 'var(--space-4)' }}>
              <div style={{ padding: 'var(--space-3)', background: 'var(--color-primary-surface)', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>
                  Holland Code: {assessment.holland_code}
                </span>
              </div>
            </div>
            {Object.entries(assessment.scores).map(([dim, score]) => (
              <div className="trait-row" key={dim}>
                <span className="trait-row__label">{dim}</span>
                <div className="trait-row__bar" role="progressbar" aria-valuenow={score} aria-valuemin={0} aria-valuemax={maxScore} aria-label={DIMENSION_LABELS[dim] ?? dim}>
                  <div className="trait-row__fill" style={{ width: `${maxScore > 0 ? (score / maxScore) * 100 : 0}%` }} />
                </div>
                <span className="trait-row__score">{score}</span>
              </div>
            ))}
          </>
        ) : (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {profile.first_name} hasn't completed the career quiz yet.
          </p>
        )}
      </div>

      {/* Career Pathways */}
      {assessment && assessment.recommendations.length > 0 && (
        <div className="child-detail__section">
          <h2 className="child-detail__section-title">Best career pathways</h2>
          {assessment.recommendations.map((rec) => (
            <div className="pathway-row" key={rec.rank}>
              <div className={`pathway-row__rank pathway-row__rank--${rec.rank}`}>
                {rec.rank}
              </div>
              <div className="pathway-row__info">
                <div className="pathway-row__name">{rec.pathway.name}</div>
                <div className="pathway-row__desc">{rec.pathway.description}</div>
              </div>
              <div className="pathway-row__pct">{rec.fit_pct}%</div>
            </div>
          ))}
        </div>
      )}

      {/* Grades */}
      <div className="child-detail__section">
        <h2 className="child-detail__section-title">{profile.first_name}'s grades</h2>
        {subjects.length > 0 ? (
          subjects.map((subj) => (
            <div className="subject-row" key={subj.id}>
              <div>
                <div className="subject-row__name">{subj.name}</div>
                <div style={{ fontSize: 'var(--font-size-xs, 0.75rem)', color: 'var(--color-text-secondary)' }}>
                  {subj.category}
                </div>
              </div>
              <div className="subject-row__grades">
                {subj.grades.length > 0
                  ? subj.grades.map((g) => (
                      <span className="grade-badge" key={g.id}>
                        T{g.term}: {g.level}
                      </span>
                    ))
                  : <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>No grades</span>
                }
              </div>
            </div>
          ))
        ) : (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {profile.first_name} hasn't enrolled in any subjects yet.
          </p>
        )}
      </div>

      {/* Counselor */}
      <div className="child-detail__section">
        <h2 className="child-detail__section-title">Counselor</h2>
        {counselor ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: latest_note ? 'var(--space-4)' : 0 }}>
              <div
                style={{
                  width: 40, height: 40, borderRadius: '50%',
                  background: 'var(--color-primary-surface)', color: 'var(--color-primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: 'var(--font-size-sm)',
                }}
                aria-hidden="true"
              >
                {initials(counselor.first_name, counselor.last_name)}
              </div>
              <div>
                <div style={{ fontWeight: 'var(--font-weight-medium)' }}>
                  {counselor.first_name} {counselor.last_name}
                </div>
                <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                  {counselor.email}
                </div>
              </div>
            </div>
            {latest_note ? (
              <div style={{ padding: 'var(--space-3)', background: 'var(--color-primary-surface)', borderRadius: 'var(--radius-md)' }}>
                <p style={{ fontStyle: 'italic', color: 'var(--color-text)', marginBottom: 'var(--space-2)' }}>
                  "{latest_note.body}"
                </p>
                <p style={{ fontSize: 'var(--font-size-xs, 0.75rem)', color: 'var(--color-text-secondary)' }}>
                  {new Date(latest_note.created_at).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })}
                </p>
              </div>
            ) : (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', fontStyle: 'italic' }}>
                No notes from the counselor yet.
              </p>
            )}
          </div>
        ) : (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            No counselor assigned yet.
          </p>
        )}
      </div>
    </div>
  )
}
