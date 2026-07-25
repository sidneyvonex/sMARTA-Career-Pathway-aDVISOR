import { Link } from 'react-router-dom'
import { LightbulbIcon } from './icons'

export default function LandingSpotlight() {
  return (
    <section className="landing-section">
      <div className="landing-spotlight">
        <LightbulbIcon className="landing-spotlight__icon" />
        <div>
          <h2 className="landing-section__heading">The RIASEC Assessment</h2>
          <p className="landing-spotlight__meta">Free &bull; 15 minutes</p>
          <p>
            Answer questions about your interests and get ranked pathway recommendations
            based on how you scored across all 6 RIASEC dimensions.
          </p>
          <Link to="/register" className="landing-spotlight__cta">
            Start Assessment
          </Link>
        </div>
      </div>
    </section>
  )
}
