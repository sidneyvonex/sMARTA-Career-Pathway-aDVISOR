import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LandingPurpose from '../components/landing/LandingPurpose'
import LandingBand from '../components/landing/LandingBand'
import LandingPathwayGrid, { PATHWAYS } from '../components/landing/LandingPathwayGrid'
import LandingSpotlight from '../components/landing/LandingSpotlight'
import LandingCTA from '../components/landing/LandingCTA'
import LandingFooter from '../components/landing/LandingFooter'
import { RoadmapIcon } from '../components/landing/icons'

function withRouter(ui: React.ReactElement) {
  return render(ui, { wrapper: MemoryRouter })
}

describe('LandingPurpose', () => {
  it('renders the honest stat callouts', () => {
    withRouter(<LandingPurpose />)
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText(/cbc pathways/i)).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
    expect(screen.getByText(/riasec dimensions/i)).toBeInTheDocument()
  })
})

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

  it('renders a card per pathway plus a text-only assessment CTA tile', () => {
    withRouter(<LandingPathwayGrid />)
    expect(screen.getByRole('heading', { name: 'STEM' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Social Sciences' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Arts & Sports Science' })).toBeInTheDocument()
    const assessmentLink = screen.getByRole('link', { name: /take the riasec assessment/i })
    expect(assessmentLink).toHaveAttribute('href', '/register')
  })
})

describe('LandingSpotlight', () => {
  it('renders the free assessment callout with a CTA to /register', () => {
    withRouter(<LandingSpotlight />)
    expect(screen.getByText(/free/i)).toBeInTheDocument()
    expect(screen.getByText(/15 minutes/i)).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /start assessment/i })
    expect(cta).toHaveAttribute('href', '/register')
  })
})

describe('LandingCTA', () => {
  it('renders the closing call to action linking to /register', () => {
    withRouter(<LandingCTA />)
    expect(screen.getByText(/ready to find your path/i)).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /register|create.*account/i })
    expect(cta).toHaveAttribute('href', '/register')
  })
})

describe('LandingFooter', () => {
  it('renders the wordmark bookend and nav links', () => {
    withRouter(<LandingFooter />)
    expect(screen.getByText('Smarta Shauri')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /login/i })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: /register/i })).toHaveAttribute('href', '/register')
  })
})
