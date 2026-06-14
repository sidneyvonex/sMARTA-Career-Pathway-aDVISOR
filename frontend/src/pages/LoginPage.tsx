import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const setUser = useAuthStore((s) => s.setUser)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authApi.login(email, password)
      setUser(res.data.data.user)
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.message ?? 'Login failed. Check your email and password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: '4rem auto', padding: '0 1rem' }}>
      <h1 style={{ color: '#006B3F', marginBottom: '1.5rem' }}>Sign in</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="email" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Email</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email"
            style={{ width: '100%', padding: '0.75rem', border: '1px solid #E0E0E0', borderRadius: 6, fontSize: '1rem', boxSizing: 'border-box' }} />
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="password" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Password</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password"
            style={{ width: '100%', padding: '0.75rem', border: '1px solid #E0E0E0', borderRadius: 6, fontSize: '1rem', boxSizing: 'border-box' }} />
        </div>
        <button type="submit" disabled={loading}
          style={{ width: '100%', padding: '0.875rem', background: '#006B3F', color: '#fff', border: 'none', borderRadius: 6, fontSize: '1rem', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 44 }}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p style={{ marginTop: '1rem', textAlign: 'center' }}>
        <Link to="/forgot-password" style={{ color: '#006B3F' }}>Forgot password?</Link>
      </p>
      <p style={{ textAlign: 'center' }}>
        New student? <Link to="/register" style={{ color: '#006B3F', fontWeight: 500 }}>Create account</Link>
      </p>
    </main>
  )
}
