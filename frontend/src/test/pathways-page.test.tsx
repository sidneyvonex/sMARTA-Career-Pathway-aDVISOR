// frontend/src/test/pathways-page.test.tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PathwaysPage from '../pages/PathwaysPage'

test('Pathways page shows all three pathway names', () => {
  render(<MemoryRouter><PathwaysPage /></MemoryRouter>)
  expect(screen.getByRole('heading', { name: 'STEM' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Social Sciences' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Arts & Sports Science' })).toBeInTheDocument()
})
