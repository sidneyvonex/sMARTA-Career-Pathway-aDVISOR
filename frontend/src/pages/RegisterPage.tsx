import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
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

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '0.75rem', border: '1px solid #E0E0E0',
    borderRadius: 6, fontSize: '1rem', boxSizing: 'border-box',
  }

  return (
    <main style={{ maxWidth: 480, margin: '3rem auto', padding: '0 1rem' }}>
      <h1 style={{ color: '#006B3F', marginBottom: '1.5rem' }}>Create your account</h1>
      <form onSubmit={handleSubmit}>
        {[
          { id: 'first_name', label: 'First name', type: 'text', autoComplete: 'given-name' },
          { id: 'last_name', label: 'Last name', type: 'text', autoComplete: 'family-name' },
          { id: 'email', label: 'Email', type: 'email', autoComplete: 'email' },
          { id: 'password', label: 'Password (min 8 characters)', type: 'password', autoComplete: 'new-password' },
        ].map(({ id, label, type, autoComplete }) => (
          <div key={id} style={{ marginBottom: '1rem' }}>
            <label htmlFor={id} style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>{label}</label>
            <input id={id} type={type} autoComplete={autoComplete} required
              value={form[id as keyof typeof form]} onChange={set(id)} style={inputStyle} />
          </div>
        ))}
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="county" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>County</label>
          <select id="county" required value={form.county} onChange={set('county')}
            style={{ ...inputStyle, background: '#fff' }}>
            <option value="">Select your county</option>
            {COUNTIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="grade" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Grade</label>
          <select id="grade" value={form.grade} onChange={set('grade')} style={{ ...inputStyle, background: '#fff' }}>
            <option value="9">Grade 9</option>
            <option value="10">Grade 10</option>
          </select>
        </div>
        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="school_code" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
            School code <span style={{ fontWeight: 400, color: '#666' }}>(optional — leave blank for self-guided)</span>
          </label>
          <input id="school_code" type="text" value={form.school_code} onChange={set('school_code')} style={inputStyle} />
        </div>
        <button type="submit" disabled={loading}
          style={{ width: '100%', padding: '0.875rem', background: '#006B3F', color: '#fff',
            border: 'none', borderRadius: 6, fontSize: '1rem', fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer', minHeight: 44 }}>
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '1rem' }}>
        Already have an account? <Link to="/login" style={{ color: '#006B3F', fontWeight: 500 }}>Sign in</Link>
      </p>
    </main>
  )
}
