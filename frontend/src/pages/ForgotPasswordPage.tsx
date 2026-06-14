import { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
import { authApi } from '../api/auth'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.requestPasswordReset(email)
      setSubmitted(true)
    } catch {
      toast.error('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <AuthLayout heading="Check your email" subheading="A reset link is on its way.">
        <div className="auth-status success">
          If an account with <strong>{email}</strong> exists, we've sent a password reset link. It expires in 1 hour.
        </div>
        <div style={{ marginTop: 'var(--space-6)', textAlign: 'center' }}>
          <Link to="/login" style={{ fontSize: 'var(--font-size-sm)' }}>← Back to sign in</Link>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      heading="Forgot your password?"
      subheading="Enter your email and we'll send you a reset link"
      footer={<span><Link to="/login">← Back to sign in</Link></span>}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Sending…' : 'Send reset link'}
        </button>
      </form>
    </AuthLayout>
  )
}
