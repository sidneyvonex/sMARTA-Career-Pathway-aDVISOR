import { Link } from 'react-router-dom'
import type { EducationGoal } from '../../api/tertiary'
import LoadingSkeleton from '../common/dashboard/LoadingSkeleton'


interface Props {
  goals: EducationGoal[]
  isLoading?: boolean
}


function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(value))
}


export default function EducationGoalPreview({ goals, isLoading = false }: Props) {
  return (
    <section className="progress-panel progress-education" aria-labelledby="education-goal-preview-title">
      <div className="progress-section-heading">
        <div>
          <h2 id="education-goal-preview-title">Education goal preview</h2>
          <p>Exploration choices stay separate from your academic targets.</p>
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton label="Loading education goals" rows={2} variant="list" />
      ) : goals.length === 0 ? (
        <p className="progress-panel__empty">No education goal has been saved yet.</p>
      ) : (
        <div className="progress-education__list">
          {goals.slice(0, 3).map((goal) => {
            const provenance = goal.programme ?? goal.institution
            const verification = provenance.verification_status === 'historical'
              ? 'Historical'
              : provenance.verification_status === 'verified' ? 'Verified' : 'Unavailable'
            return (
              <article className="progress-education__goal" key={goal.id}>
                <span>{goal.kind === 'primary' ? 'Primary exploration' : `Alternative ${goal.priority}`}</span>
                <h3>{goal.institution.name}</h3>
                <p>{goal.programme?.name ?? 'Institution-wide exploration'}</p>
                <small>
                  {provenance.education_framework} · {provenance.admission_cycle} · Effective {displayDate(provenance.effective_date)} · Verification: {verification}
                  {provenance.verification_status === 'historical' ? ' · Historical reference only' : ''}
                </small>
                <a href={provenance.source_url} target="_blank" rel="noreferrer" className="education-reference-source">
                  Open {goal.programme ? 'programme' : 'institution'} source
                </a>
              </article>
            )
          })}
        </div>
      )}
      <p className="progress-education__note">
        Education goals support exploration. They do not determine official placement or admission.
      </p>
      <Link className="student-action student-action--secondary progress-education__link" to="/education-goals">
        Explore education goals
      </Link>
    </section>
  )
}
