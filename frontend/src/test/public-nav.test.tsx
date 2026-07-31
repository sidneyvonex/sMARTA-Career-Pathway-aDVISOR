import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

test('starts the keyboard path with a skip link before public navigation', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><PublicNav /></MemoryRouter>)

  const skipLink = screen.getByRole('link', { name: 'Skip to main content' })
  expect(skipLink).toHaveAttribute('href', '#main-content')

  await user.tab()
  expect(skipLink).toHaveFocus()

  await user.tab()
  expect(screen.getByRole('link', { name: 'placements.education.go.ke' })).toHaveFocus()
})
