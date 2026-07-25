import { Link } from 'react-router-dom'

export default function LandingCTA() {
  return (
    <section className="landing-section">
      <div className="landing-cta-banner">
        <h2 className="landing-section__heading">Ready to find your path?</h2>
        <Link to="/register" className="landing-hero__badge">
          Create your free account
        </Link>
      </div>
    </section>
  )
}
