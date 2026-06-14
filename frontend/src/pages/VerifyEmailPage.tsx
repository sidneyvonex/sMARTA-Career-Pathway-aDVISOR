import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
import { authApi } from '../api/auth'

type VerifyState = 'pending' | 'success' | 'error' | 'inbox'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
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
    setResending(true)
    try {
      await authApi.resendVerification()
      toast.success('Verification email sent.')
    } catch {
      toast.error('Could not resend. Please try again.')
    } finally {
      setResending(false)
    }
  }

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
      <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Didn't receive it?</span>
        <button className="btn-ghost" onClick={resend} disabled={resending}>
          {resending ? 'Sending…' : 'Resend email'}
        </button>
      </div>
    </AuthLayout>
  )
}
