import { Link } from 'react-router-dom'
import { CompassIcon, LightbulbIcon, NetworkIcon } from './icons'

export default function LandingHero() {
  return (
    <section className="landing-hero">
      <div className="landing-hero__icons">
        <CompassIcon />
        <LightbulbIcon />
        <NetworkIcon />
      </div>
      <h1 className="landing-hero__wordmark">Smarta Shauri</h1>
      <p className="landing-hero__tagline">Discover. Plan. Choose. Succeed.</p>
      <Link to="/register" className="landing-hero__badge">
        Get Started
      </Link>
    </section>
  )
}
