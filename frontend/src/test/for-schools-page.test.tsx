import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ForSchoolsPage from '../pages/ForSchoolsPage'

test('For Schools shows three plan tiers', () => {
  render(<MemoryRouter><ForSchoolsPage /></MemoryRouter>)
  expect(screen.getByRole('heading', { name: 'Free' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'School License' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Individual Premium' })).toBeInTheDocument()
})
