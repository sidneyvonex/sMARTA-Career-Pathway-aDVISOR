import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
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
      toast.error(err.response?.data?.message ?? 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      heading="Welcome back"
      subheading="Sign in to your CBC Guidance account"
      footer={<span>Don't have an account? <Link to="/register">Create one</Link></span>}
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

        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <span className="form-hint" style={{ textAlign: 'right' }}>
            <Link to="/forgot-password" style={{ fontSize: 'var(--font-size-xs)' }}>Forgot password?</Link>
          </span>
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </AuthLayout>
  )
}
