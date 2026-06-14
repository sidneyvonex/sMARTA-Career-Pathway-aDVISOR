import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
)

describe('LoginPage', () => {
  it('renders email and password fields', () => {
    render(<LoginPage />, { wrapper: Wrapper })
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('shows sign in button', () => {
    render(<LoginPage />, { wrapper: Wrapper })
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('disables button while submitting', async () => {
    render(<LoginPage />, { wrapper: Wrapper })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'TestPass123!' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(screen.getByRole('button')).toBeDisabled())
  })
})

describe('RegisterPage', () => {
  it('renders all required fields', () => {
    render(<RegisterPage />, { wrapper: Wrapper })
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/county/i)).toBeInTheDocument()
  })

  it('renders county options', () => {
    render(<RegisterPage />, { wrapper: Wrapper })
    expect(screen.getByText('Kiambu')).toBeInTheDocument()
    expect(screen.getByText("Murang'a")).toBeInTheDocument()
  })
})
