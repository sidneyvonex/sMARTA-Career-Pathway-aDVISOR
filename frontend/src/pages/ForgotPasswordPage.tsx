import { useState } from 'react'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await authApi.requestPasswordReset(email)
      setSubmitted(true)
    } catch {
      toast.error('Something went wrong. Please try again.')
    }
  }

  if (submitted) {
    return (
      <main style={{ maxWidth: 480, margin: '4rem auto', padding: '0 1rem', textAlign: 'center' }}>
        <h1 style={{ color: '#006B3F' }}>Check your email</h1>
        <p>If an account with that email exists, we've sent a password reset link.</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 400, margin: '4rem auto', padding: '0 1rem' }}>
      <h1 style={{ color: '#006B3F', marginBottom: '1.5rem' }}>Reset your password</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="email" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Email</label>
          <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: '0.75rem', border: '1px solid #E0E0E0', borderRadius: 6, fontSize: '1rem', boxSizing: 'border-box' }} />
        </div>
        <button type="submit"
          style={{ width: '100%', padding: '0.875rem', background: '#006B3F', color: '#fff', border: 'none', borderRadius: 6, fontSize: '1rem', fontWeight: 600, cursor: 'pointer', minHeight: 44 }}>
          Send reset link
        </button>
      </form>
    </main>
  )
}
