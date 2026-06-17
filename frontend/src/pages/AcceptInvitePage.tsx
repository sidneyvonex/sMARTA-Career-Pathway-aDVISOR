import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

const COUNTIES = [
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
]

export default function AcceptInvitePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const setUser = useAuthStore((s) => s.setUser)
  const token = searchParams.get('token') ?? ''
  const [form, setForm] = useState({ first_name: '', last_name: '', county: '', password: '' })
  const [loading, setLoading] = useState(false)

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authApi.acceptInvite({ ...form, token })
      setUser(res.data.data.user)
      toast.success('Welcome to Smarta Shauri!')
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.message ?? 'Could not activate account. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <AuthLayout heading="Invalid invite">
        <div className="auth-status error">
          This invite link is invalid or has expired. Ask for a new one to be sent.
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout heading="Set up your account" subheading="You've been invited to Smarta Shauri">
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="first_name">First name</label>
            <input id="first_name" type="text" required autoComplete="given-name"
              placeholder="Jane" value={form.first_name} onChange={set('first_name')} />
          </div>
          <div className="form-field">
            <label htmlFor="last_name">Last name</label>
            <input id="last_name" type="text" required autoComplete="family-name"
              placeholder="Doe" value={form.last_name} onChange={set('last_name')} />
          </div>
        </div>

        <div className="form-field">
          <label htmlFor="county">County</label>
          <select id="county" required value={form.county} onChange={set('county')}>
            <option value="">Select your county</option>
            {COUNTIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="password">Create a password</label>
          <input id="password" type="password" required autoComplete="new-password"
            placeholder="At least 8 characters" value={form.password} onChange={set('password')} />
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Activating…' : 'Activate account'}
        </button>
      </form>
    </AuthLayout>
  )
}
