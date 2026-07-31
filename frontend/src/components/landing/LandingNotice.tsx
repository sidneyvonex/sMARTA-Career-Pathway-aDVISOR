export default function LandingNotice() {
  return (
    <section className="landing-section">
      <div className="landing-notice">
        <span className="landing-eyebrow">Important</span>
        <h2 className="landing-section__heading" style={{ marginTop: '0.75rem' }}>
          We guide the decision.
          <span className="landing-script" style={{ color: 'var(--color-flame)', display: 'inline' }}>
            {' '}
            You make it official.
          </span>
        </h2>
        <p className="landing-section__lede" style={{ marginTop: '1rem', maxWidth: '60ch' }}>
          Smarta Shauri helps you understand your RIASEC interests, explore CBC pathways, and
          review your subject options. It does not predict success or make placement decisions.
          It is a decision-support tool, not a government system — it doesn&apos;t submit anything
          to KNEC or the Ministry of Education on your behalf.
        </p>

        <div className="landing-notice__grid">
          <div className="landing-notice-card landing-notice-card--us">
            <p className="landing-notice-card__label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3 11.2c.6.4 1 1.1 1 1.8h4c0-.7.4-1.4 1-1.8A6 6 0 0 0 12 3z" />
              </svg>
              What Smarta Shauri does
            </p>
            <ul>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Scores your free RIASEC interest assessment
              </li>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Ranks the 3 CBC pathways by alignment with the interests you shared
              </li>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Tracks your subject grades every term
              </li>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Gives your counselor and parent the same picture, so you&apos;re not deciding alone
              </li>
            </ul>
          </div>
          <div className="landing-notice-card landing-notice-card--gov">
            <p className="landing-notice-card__label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <rect x="3" y="4" width="18" height="16" rx="2" />
                <path d="M8 2v4M16 2v4M3 10h18" />
              </svg>
              What still happens with the Ministry of Education
            </p>
            <ul>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                You sit the official KJSEA assessment through your school
              </li>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                You submit your official Senior School pathway choices at{' '}
                <strong>selection.education.go.ke</strong>
              </li>
              <li>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                The Ministry handles final placement. Confirm the current cohort&apos;s criteria,
                deadlines, and results on its official services
              </li>
            </ul>
          </div>
        </div>

        <div className="landing-notice__cta">
          <a
            className="mk-btn mk-btn-dark"
            href="https://selection.education.go.ke"
            target="_blank"
            rel="noopener noreferrer"
          >
            Apply officially
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
              <path d="M7 17L17 7M9 7h8v8" />
            </svg>
          </a>
          <a
            className="mk-btn mk-btn-outline"
            href="https://kjsea.knec.ac.ke"
            target="_blank"
            rel="noopener noreferrer"
          >
            Check KJSEA results
          </a>
        </div>
        <p className="landing-notice__fine">
          Smarta Shauri is an independent student project and is not affiliated with,
          endorsed by, or operated by KNEC or the Ministry of Education. Always confirm
          deadlines and requirements on their official channels. Official service links
          checked 31 July 2026.
        </p>
      </div>
    </section>
  )
}
