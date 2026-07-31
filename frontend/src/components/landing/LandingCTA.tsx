import { Link } from 'react-router-dom'

export default function LandingCTA() {
  return (
    <section className="landing-section">
      <div className="landing-cta-band">
        <span className="landing-eyebrow">Last step</span>
        <p className="landing-cta-band__heading">
          Your next pathway conversation starts here.
          <span className="landing-script"> Let&apos;s explore the options.</span>
        </p>
        <p className="landing-cta-band__sub">Free forever. Takes about 15 minutes.</p>
        <Link to="/register" className="mk-btn mk-btn-dark">
          Create your free account
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </Link>
      </div>
    </section>
  )
}
