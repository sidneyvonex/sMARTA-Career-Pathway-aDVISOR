import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PublicFooter from '../components/marketing/PublicFooter'

test('footer links to For Schools and Register', () => {
  render(<MemoryRouter><PublicFooter /></MemoryRouter>)
  expect(screen.getByRole('link', { name: 'For Schools' })).toHaveAttribute('href', '/for-schools')
  expect(screen.getByRole('link', { name: 'Register' })).toHaveAttribute('href', '/register')
})
