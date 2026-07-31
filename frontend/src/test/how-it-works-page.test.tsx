import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import HowItWorksPage from '../pages/HowItWorksPage'

test('How It Works shows the six RIASEC dimensions', () => {
  render(
    <MemoryRouter>
      <HowItWorksPage />
    </MemoryRouter>
  )
  expect(
    screen.getByRole('heading', {
      level: 1,
      name: /from confused to confident/i,
    }),
  ).toBeInTheDocument()
  ;['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional'].forEach((d) =>
    expect(screen.getByRole('heading', { name: d })).toBeInTheDocument()
  )
})

test('How It Works shows the implemented five-stage learner journey', () => {
  render(
    <MemoryRouter>
      <HowItWorksPage />
    </MemoryRouter>
  )
  ;['Evidence', 'Interests', 'Compare', 'Plan', 'Review'].forEach((step) =>
    expect(screen.getByRole('heading', { name: step })).toBeInTheDocument()
  )
  expect(screen.getAllByText(/five-county rollout/i).length).toBeGreaterThan(0)
})
