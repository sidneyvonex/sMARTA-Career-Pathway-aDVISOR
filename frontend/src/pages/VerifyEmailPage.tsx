import { useState } from 'react'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'

export default function VerifyEmailPage() {
  const [sent, setSent] = useState(false)

  const resend = async () => {
    try {
      await authApi.resendVerification()
      setSent(true)
      toast.success('Verification email sent.')
    } catch {
      toast.error('Could not resend. Please try again.')
    }
  }

  return (
    <main style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
      <h1 style={{ color: '#006B3F' }}>Check your email</h1>
      <p>We've sent a verification link to your email address. Click the link to activate your account.</p>
      {!sent && (
        <p>
          Didn't receive it?{' '}
          <button onClick={resend} style={{ background: 'none', border: 'none', color: '#006B3F', cursor: 'pointer', fontWeight: 500, fontSize: '1rem', padding: 0 }}>
            Resend verification email
          </button>
        </p>
      )}
    </main>
  )
}
