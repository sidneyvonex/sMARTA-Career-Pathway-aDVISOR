import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LandingHero from '../components/landing/LandingHero'

describe('LandingHero', () => {
  it('renders the wordmark, tagline, and a CTA linking to /register', () => {
    render(<LandingHero />, { wrapper: MemoryRouter })
    expect(screen.getByRole('heading', { level: 1, name: /smarta shauri/i })).toBeInTheDocument()
    expect(screen.getByText(/discover\. plan\. choose\. succeed\./i)).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /get started/i })
    expect(cta).toHaveAttribute('href', '/register')
  })
})
