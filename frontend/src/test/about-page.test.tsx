// frontend/src/test/about-page.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import AboutPage from '../pages/AboutPage'

describe('AboutPage', () => {
  it('renders an h1 and a link to /register', () => {
    render(<AboutPage />, { wrapper: MemoryRouter })

    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /every learner deserves a real answer/i,
      }),
    ).toBeInTheDocument()
    expect(
      screen.getAllByRole('link').some((a) => a.getAttribute('href') === '/register')
    ).toBe(true)
  })
})
