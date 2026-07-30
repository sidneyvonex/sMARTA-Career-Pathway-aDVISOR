import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LandingPurpose from '../components/landing/LandingPurpose'
import LandingBand from '../components/landing/LandingBand'
import LandingPathwayGrid, { PATHWAYS } from '../components/landing/LandingPathwayGrid'
import LandingSpotlight from '../components/landing/LandingSpotlight'
import LandingSteps from '../components/landing/LandingSteps'
import LandingNotice from '../components/landing/LandingNotice'
import LandingCommunity from '../components/landing/LandingCommunity'
import LandingCTA from '../components/landing/LandingCTA'
import LandingFooter from '../components/landing/LandingFooter'
import { RoadmapIcon } from '../components/landing/icons'

function withRouter(ui: React.ReactElement) {
  return render(ui, { wrapper: MemoryRouter })
}

describe('LandingPurpose', () => {
  it('renders the "Our work" statement and the 3 honest stat callouts', () => {
    withRouter(<LandingPurpose />)
    expect(screen.getByText(/three pathways/i)).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText(/cbc pathways/i)).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
    expect(screen.getByText(/riasec dimensions/i)).toBeInTheDocument()
    expect(screen.getByText(/to get started/i)).toBeInTheDocument()
  })
})

// LandingBand is superseded by the v4 color-band sections but the component
// itself is unchanged and still renders correctly in isolation.
describe('LandingBand', () => {
  it('renders the passed heading and icon inside the correct variant class', () => {
    const { container } = render(
      <LandingBand variant="dark" icon={<RoadmapIcon />} heading="Less Confusion. Clearer Choices." />
    )
    expect(container.querySelector('.landing-band--dark')).toBeInTheDocument()
    expect(screen.getByText('Less Confusion. Clearer Choices.')).toBeInTheDocument()
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})

describe('LandingPathwayGrid', () => {
  it('exports exactly the 3 seeded CBC pathways', () => {
    expect(PATHWAYS.map((p) => p.name)).toEqual(['STEM', 'Social Sciences', 'Arts & Sports Science'])
  })

  it('renders a photo card per pathway plus a "not sure yet" assessment CTA', () => {
    withRouter(<LandingPathwayGrid />)
    expect(screen.getByRole('heading', { name: 'STEM' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Social Sciences' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Arts & Sports Science' })).toBeInTheDocument()
    const images = screen.getAllByRole('img')
    expect(images.length).toBeGreaterThanOrEqual(3)
    images.forEach((img) => {
      expect(img).toHaveAttribute('src', expect.stringMatching(/^\/img\//))
    })
    const assessmentLink = screen.getByRole('link', { name: /take the riasec assessment/i })
    expect(assessmentLink).toHaveAttribute('href', '/register')
  })
})

describe('LandingSpotlight', () => {
  it('renders the featured RIASEC assessment card with a CTA to /register', () => {
    withRouter(<LandingSpotlight />)
    expect(screen.getByText(/riasec assessment/i)).toBeInTheDocument()
    expect(screen.getAllByText(/free/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/15 min/i)).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /start assessment/i })
    expect(cta).toHaveAttribute('href', '/register')
  })
})

describe('LandingSteps', () => {
  it('renders 4 numbered step tiles without promising an outcome', () => {
    withRouter(<LandingSteps />)
    expect(screen.getByRole('heading', { name: 'Discover' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Plan' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Choose' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Reflect' })).toBeInTheDocument()
    expect(screen.getByText('01')).toBeInTheDocument()
    expect(screen.getByText('04')).toBeInTheDocument()
  })
})

describe('LandingNotice', () => {
  it('explains Smarta Shauri is decision support and links to the official application portals', () => {
    withRouter(<LandingNotice />)
    expect(screen.getByText(/decision-support tool/i)).toBeInTheDocument()
    const applyLink = screen.getByRole('link', { name: /apply officially/i })
    expect(applyLink).toHaveAttribute('href', 'https://placements.education.go.ke')
    const resultsLink = screen.getByRole('link', { name: /check kjsea results/i })
    expect(resultsLink).toHaveAttribute('href', 'https://kjsea.knec.ac.ke')
  })
})

describe('LandingCommunity', () => {
  it('renders under id="community" with 8 hover-detail school cards', () => {
    const { container } = withRouter(<LandingCommunity />)
    expect(container.querySelector('#community')).toBeInTheDocument()
    expect(screen.getByText('Chinga Boys High School')).toBeInTheDocument()
    expect(screen.getByText('Mahiga Girls Secondary School')).toBeInTheDocument()
    const images = screen.getAllByRole('img')
    expect(images).toHaveLength(8)
    images.forEach((img) => {
      expect(img).toHaveAttribute('src', expect.stringMatching(/^\/img\//))
    })
  })
})

describe('LandingCTA', () => {
  it('renders the closing call to action linking to /register', () => {
    withRouter(<LandingCTA />)
    expect(screen.getByText(/your pathway is already out there/i)).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /create your free account/i })
    expect(cta).toHaveAttribute('href', '/register')
  })
})

// LandingFooter is superseded by PublicFooter on the live page, but the
// component itself is unchanged and still renders correctly in isolation.
describe('LandingFooter', () => {
  it('renders the wordmark bookend and nav links', () => {
    withRouter(<LandingFooter />)
    expect(screen.getByText('Smarta Shauri')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /login/i })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: /register/i })).toHaveAttribute('href', '/register')
  })
})
