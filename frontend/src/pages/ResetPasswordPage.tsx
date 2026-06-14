import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') ?? ''
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.confirmPasswordReset(token, password)
      toast.success('Password reset. Please log in.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.message ?? 'Reset failed. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) return <p style={{ padding: '2rem' }}>Invalid reset link.</p>

  return (
    <main style={{ maxWidth: 400, margin: '4rem auto', padding: '0 1rem' }}>
      <h1 style={{ color: '#006B3F', marginBottom: '1.5rem' }}>Set new password</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="password" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
            New password (min 8 characters)
          </label>
          <input id="password" type="password" required minLength={8} value={password}
            onChange={(e) => setPassword(e.target.value)} autoComplete="new-password"
            style={{ width: '100%', padding: '0.75rem', border: '1px solid #E0E0E0', borderRadius: 6, fontSize: '1rem', boxSizing: 'border-box' }} />
        </div>
        <button type="submit" disabled={loading}
          style={{ width: '100%', padding: '0.875rem', background: '#006B3F', color: '#fff', border: 'none', borderRadius: 6, fontSize: '1rem', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 44 }}>
          {loading ? 'Resetting…' : 'Reset password'}
        </button>
      </form>
    </main>
  )
}
