import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LandingHero from '../components/landing/LandingHero'

describe('LandingHero', () => {
  it('renders the Discover/Plan/Choose/Succeed heading as the page h1', () => {
    render(<LandingHero />, { wrapper: MemoryRouter })
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent(/discover\.\s*plan\.\s*choose\.\s*succeed\./i)
  })

  it('renders a "Get Started" CTA linking to /register', () => {
    render(<LandingHero />, { wrapper: MemoryRouter })
    const cta = screen.getByRole('link', { name: /get started/i })
    expect(cta).toHaveAttribute('href', '/register')
  })

  it('renders a "See the pathways" CTA linking to /pathways', () => {
    render(<LandingHero />, { wrapper: MemoryRouter })
    const cta = screen.getByRole('link', { name: /see the pathways/i })
    expect(cta).toHaveAttribute('href', '/pathways')
  })

  it('frames interest results as advisory alignment within the five-county pilot', () => {
    render(<LandingHero />, { wrapper: MemoryRouter })
    expect(screen.getByText(/five-county pilot/i)).toBeInTheDocument()
    expect(screen.getByText(/align with the interests you shared/i)).toBeInTheDocument()
    expect(screen.queryByText(/actually fits you/i)).not.toBeInTheDocument()
  })

  it('renders the photo filmstrip with images served from /img/', () => {
    render(<LandingHero />, { wrapper: MemoryRouter })
    const images = screen.getAllByRole('img')
    expect(images.length).toBeGreaterThanOrEqual(3)
    images.forEach((img) => {
      expect(img).toHaveAttribute('src', expect.stringMatching(/^\/img\//))
    })
  })
})
