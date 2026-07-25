import LandingHero from '../components/landing/LandingHero'
import LandingTicker from '../components/landing/LandingTicker'
import LandingPurpose from '../components/landing/LandingPurpose'
import LandingBand from '../components/landing/LandingBand'
import LandingPathwayGrid from '../components/landing/LandingPathwayGrid'
import LandingSpotlight from '../components/landing/LandingSpotlight'
import LandingCTA from '../components/landing/LandingCTA'
import LandingFooter from '../components/landing/LandingFooter'
import { RoadmapIcon } from '../components/landing/icons'
import '../styles/landing.css'

export default function LandingPage() {
  return (
    <div className="landing-page">
      <LandingHero />
      <LandingTicker />
      <LandingPurpose />
      <LandingBand variant="dark" icon={<RoadmapIcon />} heading="Less Confusion. Clearer Choices." />
      <div id="explore-your-pathway">
        <LandingPathwayGrid />
      </div>
      <LandingSpotlight />
      <LandingBand
        variant="quote"
        icon={<RoadmapIcon />}
        heading="Every learner's path is different — yours should be too."
      />
      <LandingCTA />
      <LandingFooter />
    </div>
  )
}
