import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HowItWorksPage from '../pages/HowItWorksPage'

test('How It Works shows the six RIASEC dimensions', () => {
  render(
    <MemoryRouter>
      <HowItWorksPage />
    </MemoryRouter>
  )
  ;['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional'].forEach((d) =>
    expect(screen.getByRole('heading', { name: d })).toBeInTheDocument()
  )
})

test('How It Works shows the four process steps', () => {
  render(
    <MemoryRouter>
      <HowItWorksPage />
    </MemoryRouter>
  )
  ;['Discover', 'Plan', 'Choose', 'Succeed'].forEach((step) =>
    expect(screen.getByRole('heading', { name: step })).toBeInTheDocument()
  )
})
