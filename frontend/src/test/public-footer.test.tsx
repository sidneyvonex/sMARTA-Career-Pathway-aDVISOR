import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PublicFooter from '../components/marketing/PublicFooter'

test('footer links to For Schools and Register', () => {
  render(<MemoryRouter><PublicFooter /></MemoryRouter>)
  expect(screen.getByRole('link', { name: 'For Schools' })).toHaveAttribute('href', '/for-schools')
  expect(screen.getByRole('link', { name: 'Register' })).toHaveAttribute('href', '/register')
  expect(screen.getByText(/learners in this five-county pilot/i)).toBeInTheDocument()
  expect(screen.queryByText(/pathway is actually theirs/i)).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Official selection service' })).toHaveAttribute(
    'href',
    'https://selection.education.go.ke',
  )
  expect(screen.getByRole('link', { name: 'Placement outcomes' })).toHaveAttribute(
    'href',
    'https://placement.education.go.ke/my-placements',
  )
  expect(screen.getByRole('link', { name: 'Official subject catalogue' })).toHaveAttribute(
    'href',
    'https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf',
  )
})
