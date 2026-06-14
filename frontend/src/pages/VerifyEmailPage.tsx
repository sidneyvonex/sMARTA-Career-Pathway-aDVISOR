import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'

type State = 'pending' | 'success' | 'error' | 'resend'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [state, setState] = useState<State>(token ? 'pending' : 'resend')
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
      <main style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
        <p>Verifying your email…</p>
      </main>
    )
  }

  if (state === 'success') {
    return (
      <main style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
        <h1 style={{ color: '#006B3F' }}>Email verified</h1>
        <p>Your account is now active. <a href="/login" style={{ color: '#006B3F' }}>Sign in</a></p>
      </main>
    )
  }

  if (state === 'error') {
    return (
      <main style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
        <h1 style={{ color: '#CE1126' }}>Verification failed</h1>
        <p>The link may have expired or already been used.</p>
        <button onClick={resend} disabled={resending}
          style={{ background: 'none', border: 'none', color: '#006B3F', cursor: resending ? 'not-allowed' : 'pointer', fontWeight: 500, fontSize: '1rem', padding: 0 }}>
          {resending ? 'Sending…' : 'Request a new verification email'}
        </button>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
      <h1 style={{ color: '#006B3F' }}>Check your email</h1>
      <p>We've sent a verification link to your email address. Click the link to activate your account.</p>
      <p>
        Didn't receive it?{' '}
        <button onClick={resend} disabled={resending}
          style={{ background: 'none', border: 'none', color: '#006B3F', cursor: resending ? 'not-allowed' : 'pointer', fontWeight: 500, fontSize: '1rem', padding: 0 }}>
          {resending ? 'Sending…' : 'Resend verification email'}
        </button>
      </p>
    </main>
  )
}
