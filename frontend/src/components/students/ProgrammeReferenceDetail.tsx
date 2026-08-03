import type { ProgrammeDetail, VerificationStatus } from '../../api/tertiary'


const verificationLabels: Record<VerificationStatus, string> = {
  verified: 'Verified',
  historical: 'Historical',
  unavailable: 'Unavailable',
}

const mappingLabels: Record<ProgrammeDetail['subject_references'][number]['mapping_kind'], string> = {
  historical_requirement: 'Historical requirement',
  exploratory_alignment: 'Exploratory alignment',
}


function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(value))
}


export default function ProgrammeReferenceDetail({ programme }: { programme: ProgrammeDetail }) {
  return (
    <section
      className="education-detail"
      aria-label={`${programme.name} details`}
    >
      <header className="education-detail__header">
        <div>
          <span className="education-reference-badge">
            {programme.verification_status === 'historical' ? 'Historical reference' : 'Catalogue reference'}
          </span>
          <h2>{programme.name}</h2>
          <p>{programme.institution.name} · {programme.code}</p>
        </div>
      </header>

      <p className="education-detail__description">{programme.description}</p>

      <dl className="education-provenance" aria-label="Programme source information">
        <div><dt>Framework</dt><dd>Framework: {programme.education_framework}</dd></div>
        <div><dt>Admission cycle</dt><dd>Admission cycle: {programme.admission_cycle}</dd></div>
        <div><dt>Effective date</dt><dd>Effective date: {displayDate(programme.effective_date)}</dd></div>
        <div><dt>Verification</dt><dd>Verification: {verificationLabels[programme.verification_status]}</dd></div>
      </dl>
      <a href={programme.source_url} target="_blank" rel="noreferrer" className="education-source-link">
        Open official source
      </a>

      <div className="education-reference-section">
        <h3>Subject relevance</h3>
        {programme.subject_references.length === 0 ? (
          <p className="education-inline-empty">No subject references are available for this programme.</p>
        ) : (
          <div className="education-reference-list">
            {programme.subject_references.map((reference) => (
              <article
                key={reference.id}
                className="education-reference-item"
                aria-label={`${reference.subject_name} subject reference`}
              >
                <span>{mappingLabels[reference.mapping_kind]}</span>
                <strong>{reference.subject_name}</strong>
                <p>{reference.notes}</p>
                <small>{reference.advisory_label}</small>
                <small className="education-reference-provenance">
                  {reference.education_framework} · {reference.admission_cycle} · Effective {displayDate(reference.effective_date)} · Verification: {verificationLabels[reference.verification_status]}
                </small>
                <a href={reference.source_url} target="_blank" rel="noreferrer" className="education-reference-source">
                  Open {reference.subject_name} source
                </a>
              </article>
            ))}
          </div>
        )}
      </div>

      <div className="education-reference-section">
        <h3>Historical admission references</h3>
        {programme.historical_admission_references.length === 0 ? (
          <p className="education-inline-empty">No historical admission references are available.</p>
        ) : programme.historical_admission_references.map((reference) => (
          <article
            key={reference.id}
            className="education-historical-reference"
            aria-label="Historical admission reference"
          >
            <div>
              <strong>Historical admission reference</strong>
              <span>Reference only</span>
            </div>
            <p>{reference.requirement_summary}</p>
            <small>
              {reference.education_framework} · {reference.admission_cycle} · Effective {displayDate(reference.effective_date)} · Verification: {verificationLabels[reference.verification_status]}
            </small>
            <a href={reference.source_url} target="_blank" rel="noreferrer" className="education-reference-source">
              Open historical admission source
            </a>
          </article>
        ))}
      </div>

      <aside className="education-criteria-notice" aria-label="Official criteria unavailable">
        <strong>Official criteria unavailable</strong>
        <p>
          Official placement criteria are unavailable for this framework and catalogue reference.
          Smarta Shauri does not substitute a formula or threshold.
        </p>
      </aside>
    </section>
  )
}
