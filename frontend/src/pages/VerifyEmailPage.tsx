import { useEffect, useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

type VerifyState = 'pending' | 'success' | 'error' | 'inbox'

export default function VerifyEmailPage() {
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const user = useAuthStore((authState) => authState.user)
  const registrationEmail = (location.state as { email?: string } | null)?.email ?? ''
  const [email, setEmail] = useState(registrationEmail)
  const [state, setState] = useState<VerifyState>(token ? 'pending' : 'inbox')
  const [resending, setResending] = useState(false)

  useEffect(() => {
    if (!token) return
    authApi
      .verifyEmail(token)
      .then(() => setState('success'))
      .catch(() => setState('error'))
  }, [token])

  const resend = async () => {
    const targetEmail = user?.email ?? email.trim()
    if (!targetEmail) {
      toast.error('Enter your email address first.')
      return
    }

    setResending(true)
    try {
      await authApi.resendVerification(targetEmail)
      toast.success('If the account is awaiting verification, a new email has been sent.')
    } catch {
      toast.error('Could not resend. Please try again.')
    } finally {
      setResending(false)
    }
  }

  const emailField = !user ? (
    <div className="form-field" style={{ marginTop: 'var(--space-4)' }}>
      <label htmlFor="verification-email">Email address</label>
      <input
        id="verification-email"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="you@example.com"
      />
    </div>
  ) : null

  if (state === 'pending') {
    return (
      <AuthLayout heading="Verifying…">
        <p style={{ color: 'var(--color-text-secondary)', textAlign: 'center' }}>
          Please wait while we confirm your email address.
        </p>
      </AuthLayout>
    )
  }

  if (state === 'success') {
    return (
      <AuthLayout heading="Email verified" subheading="Your account is now active.">
        <div className="auth-status success" style={{ textAlign: 'center' }}>
          Your email was confirmed successfully.
        </div>
        <Link to="/login" className="btn-primary" style={{ display: 'block', textAlign: 'center', marginTop: 'var(--space-4)', lineHeight: '48px', textDecoration: 'none', borderRadius: 'var(--radius-md)' }}>
          Sign in
        </Link>
      </AuthLayout>
    )
  }

  if (state === 'error') {
    return (
      <AuthLayout heading="Link expired" subheading="This verification link has expired or already been used.">
        <div className="auth-status error" style={{ marginBottom: 'var(--space-4)' }}>
          Request a new link below and check your inbox.
        </div>
        {emailField}
        <button className="btn-primary" onClick={resend} disabled={resending}>
          {resending ? 'Sending…' : 'Send new verification email'}
        </button>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout heading="Check your email" subheading="We've sent a verification link to your email address.">
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', lineHeight: 'var(--line-height-relaxed)' }}>
        Click the link in the email to activate your account. It expires in 24 hours.
      </p>
      {emailField}
      <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Didn't receive it?</span>
        <button className="btn-ghost" onClick={resend} disabled={resending}>
          {resending ? 'Sending…' : 'Resend email'}
        </button>
      </div>
    </AuthLayout>
  )
}
