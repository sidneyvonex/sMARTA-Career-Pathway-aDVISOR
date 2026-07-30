import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import LandingHero from '../components/landing/LandingHero'
import LandingPurpose from '../components/landing/LandingPurpose'
import LandingSpotlight from '../components/landing/LandingSpotlight'
import LandingPathwayGrid from '../components/landing/LandingPathwayGrid'
import LandingSteps from '../components/landing/LandingSteps'
import LandingNotice from '../components/landing/LandingNotice'
import LandingCommunity from '../components/landing/LandingCommunity'
import LandingCTA from '../components/landing/LandingCTA'
import '../styles/landing.css'

export default function LandingPage() {
  return (
    <div className="landing-page">
      <PublicNav />

      <main id="main-content">
        <LandingHero />

        <div className="landing-color-band landing-color-band--white">
          <LandingPurpose />
          <div className="landing-section landing-section--tight">
            <LandingSpotlight />
          </div>
        </div>

        <div className="landing-color-band landing-color-band--green">
          <LandingPathwayGrid />
        </div>

        <div className="landing-color-band landing-color-band--ink">
          <LandingSteps />
        </div>

        <div className="landing-color-band landing-color-band--white">
          <LandingNotice />
        </div>

        <div className="landing-color-band landing-color-band--ink">
          <LandingCommunity />
        </div>

        <div className="landing-color-band landing-color-band--gold">
          <LandingCTA />
        </div>
      </main>

      <PublicFooter />
    </div>
  )
}
