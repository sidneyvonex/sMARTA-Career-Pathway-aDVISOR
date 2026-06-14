import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(document.body).toBeInTheDocument()
  })

  it('renders the home route content', () => {
    render(<App />)
    expect(screen.getByText(/CBC Career Guidance/i)).toBeInTheDocument()
  })
})
