import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
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
      toast.success('Password updated. Please sign in.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.message ?? 'Reset failed. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <AuthLayout heading="Invalid link">
        <div className="auth-status error">
          This reset link is invalid or has already been used. Request a new one from the sign-in page.
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout heading="Set a new password" subheading="Choose something strong and memorable">
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="password">New password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Updating…' : 'Update password'}
        </button>
      </form>
    </AuthLayout>
  )
}
