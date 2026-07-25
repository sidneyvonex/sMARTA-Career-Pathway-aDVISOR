import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LandingTicker from '../components/landing/LandingTicker'

describe('LandingTicker', () => {
  it('renders as a decorative, aria-hidden marquee containing the tagline words', () => {
    const { container } = render(<LandingTicker />)
    const ticker = container.querySelector('.landing-ticker')
    expect(ticker).toHaveAttribute('aria-hidden', 'true')
    expect(ticker?.textContent).toMatch(/discover/i)
    expect(ticker?.textContent).toMatch(/succeed/i)
  })
})
