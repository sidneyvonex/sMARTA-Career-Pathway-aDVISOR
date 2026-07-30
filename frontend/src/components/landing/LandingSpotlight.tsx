import { Link } from 'react-router-dom'

export default function LandingSpotlight() {
  return (
    <div className="landing-featured">
      <div className="landing-featured__media">
        <img
          src="/img/mahiga-girls.jpg"
          alt="Pupils at Mahiga Girls Secondary School, Nyeri County — a CBC Senior School"
          loading="lazy"
        />
      </div>
      <div className="landing-featured__body">
        <span className="landing-eyebrow">Featured &middot; Free assessment</span>
        <h3 className="landing-featured__title">The RIASEC Assessment.</h3>
        <p className="landing-featured__desc">
          Answer questions about your interests and see pathways suggested for exploration
          from your scores across all 6 RIASEC dimensions.
        </p>
        <div className="landing-featured__stats">
          <div>
            <span className="landing-featured__stat-label">Length</span>
            <span className="landing-featured__stat-value">15 min</span>
          </div>
          <div>
            <span className="landing-featured__stat-label">Dimensions</span>
            <span className="landing-featured__stat-value">6</span>
          </div>
          <div>
            <span className="landing-featured__stat-label">Cost</span>
            <span className="landing-featured__stat-value">Free</span>
          </div>
        </div>
        <p className="landing-featured__statement">
          One assessment. Three pathways to explore. A clearer conversation.
        </p>
        <Link to="/register" className="mk-btn mk-btn-dark landing-featured__cta">
          Start Assessment
        </Link>
      </div>
    </div>
  )
}
