// frontend/src/test/landing-page.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'

describe('LandingPage', () => {
  it('renders the hero heading, all pathway cards, community section, and every register CTA', () => {
    render(<LandingPage />, { wrapper: MemoryRouter })

    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')

    // Hero — v4 heading
    expect(
      screen.getByRole('heading', { level: 1 })
    ).toHaveTextContent(/discover\.\s*plan\.\s*choose\.\s*succeed\./i)

    // Pathway cards — 3 CBC pathways
    expect(screen.getByRole('heading', { name: 'STEM' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Social Sciences' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Arts & Sports Science' })).toBeInTheDocument()

    // Community section anchor
    expect(document.getElementById('community')).toBeInTheDocument()

    // Official-application notice links to the government portal
    const officialLink = screen.getByRole('link', { name: /apply officially/i })
    expect(officialLink).toHaveAttribute('href', 'https://placements.education.go.ke')

    // Every register CTA points to /register
    const registerLinks = screen.getAllByRole('link', { name: /register|get started|create your free account|start assessment|take the riasec assessment/i })
    expect(registerLinks.length).toBeGreaterThan(0)
    registerLinks.forEach((link) => {
      expect(link).toHaveAttribute('href', '/register')
    })

    // Nav + footer both render the brand wordmark
    expect(screen.getAllByText('Smarta Shauri').length).toBeGreaterThanOrEqual(2)
  })
})
