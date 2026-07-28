import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PublicNav from '../components/marketing/PublicNav'

test('renders brand, primary links, and toggles mobile menu', () => {
  render(<MemoryRouter><PublicNav /></MemoryRouter>)
  expect(screen.getByRole('link', { name: /smarta shauri/i })).toHaveAttribute('href', '/')
  expect(screen.getByRole('link', { name: 'About' })).toHaveAttribute('href', '/about')
  const toggle = screen.getByRole('button', { name: /toggle menu/i })
  expect(toggle).toHaveAttribute('aria-expanded', 'false')
  fireEvent.click(toggle)
  expect(toggle).toHaveAttribute('aria-expanded', 'true')
})
