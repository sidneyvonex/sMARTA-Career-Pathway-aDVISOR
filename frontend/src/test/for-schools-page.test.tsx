import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ForSchoolsPage from '../pages/ForSchoolsPage'

test('For Schools shows the implemented pilot operating workflow', () => {
  render(<MemoryRouter><ForSchoolsPage /></MemoryRouter>)
  expect(
    screen.getByRole('heading', {
      level: 1,
      name: /one journey\. clear handoffs\./i,
    }),
  ).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Approve learner links' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Assign counsellors' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Configure offerings' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Review learner plans' })).toBeInTheDocument()
  expect(
    screen.getAllByText(/Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua/i).length,
  ).toBeGreaterThan(0)
  expect(screen.queryByText('Individual Premium')).not.toBeInTheDocument()
})
