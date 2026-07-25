// frontend/src/test/landing-page.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'

describe('LandingPage', () => {
  it('renders the hero, all pathway cards, and the footer together', () => {
    render(<LandingPage />, { wrapper: MemoryRouter })
    expect(screen.getByRole('heading', { level: 1, name: /smarta shauri/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'STEM' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Social Sciences' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Arts & Sports Science' })).toBeInTheDocument()
    expect(screen.getByText(/ready to find your path/i)).toBeInTheDocument()
    expect(screen.getAllByText('Smarta Shauri').length).toBeGreaterThanOrEqual(2) // hero + footer wordmark
  })
})
