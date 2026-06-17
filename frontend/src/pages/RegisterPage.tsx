import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout'
import { authApi } from '../api/auth'

const COUNTIES = [
  { value: 'kiambu', label: 'Kiambu' },
  { value: 'muranga', label: "Murang'a" },
  { value: 'nyeri', label: 'Nyeri' },
  { value: 'kirinyaga', label: 'Kirinyaga' },
  { value: 'nyandarua', label: 'Nyandarua' },
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '', password: '', first_name: '', last_name: '',
    county: '', grade: '9', school_code: '',
  })
  const [loading, setLoading] = useState(false)

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.register({
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        county: form.county,
        grade: Number(form.grade),
        role: 'student',
        ...(form.school_code ? { school_code: form.school_code } : {}),
      })
      navigate('/verify-email')
    } catch (err: any) {
      const msg = err.response?.data?.message
      toast.error(typeof msg === 'string' ? msg : 'Registration failed. Please check your details.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      heading="Create your account"
      subheading="Join Smarta Shauri — free for all students"
      footer={<span>Already have an account? <Link to="/login">Sign in</Link></span>}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="first_name">First name</label>
            <input id="first_name" type="text" autoComplete="given-name" required
              placeholder="Jane" value={form.first_name} onChange={set('first_name')} />
          </div>
          <div className="form-field">
            <label htmlFor="last_name">Last name</label>
            <input id="last_name" type="text" autoComplete="family-name" required
              placeholder="Doe" value={form.last_name} onChange={set('last_name')} />
          </div>
        </div>

        <div className="form-field">
          <label htmlFor="email">Email address</label>
          <input id="email" type="email" autoComplete="email" required
            placeholder="you@example.com" value={form.email} onChange={set('email')} />
        </div>

        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="new-password" required
            placeholder="At least 8 characters" value={form.password} onChange={set('password')} />
        </div>

        <div className="form-row">
          <div className="form-field">
            <label htmlFor="county">County</label>
            <select id="county" required value={form.county} onChange={set('county')}>
              <option value="">Select county</option>
              {COUNTIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="grade">Grade</label>
            <select id="grade" value={form.grade} onChange={set('grade')}>
              <option value="9">Grade 9</option>
              <option value="10">Grade 10</option>
            </select>
          </div>
        </div>

        <div className="form-field">
          <label htmlFor="school_code">School code</label>
          <input id="school_code" type="text"
            placeholder="Optional — leave blank for self-guided"
            value={form.school_code} onChange={set('school_code')} />
          <span className="form-hint">Ask your school administrator for this code</span>
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthLayout>
  )
}
