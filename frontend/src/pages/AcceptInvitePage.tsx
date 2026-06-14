import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
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
      navigate('/')
      toast.success('Welcome to CBC Guidance!')
    } catch (err: any) {
      toast.error(err.response?.data?.message ?? 'Could not activate account. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) return <p style={{ padding: '2rem' }}>Invalid invite link.</p>

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '0.75rem', border: '1px solid #E0E0E0',
    borderRadius: 6, fontSize: '1rem', boxSizing: 'border-box',
  }

  return (
    <main style={{ maxWidth: 480, margin: '3rem auto', padding: '0 1rem' }}>
      <h1 style={{ color: '#006B3F', marginBottom: '1.5rem' }}>Set up your account</h1>
      <form onSubmit={handleSubmit}>
        {[
          { id: 'first_name', label: 'First name', type: 'text' },
          { id: 'last_name', label: 'Last name', type: 'text' },
          { id: 'password', label: 'Password (min 8 characters)', type: 'password' },
        ].map(({ id, label, type }) => (
          <div key={id} style={{ marginBottom: '1rem' }}>
            <label htmlFor={id} style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>{label}</label>
            <input id={id} type={type} required value={form[id as keyof typeof form]} onChange={set(id)} style={inputStyle} />
          </div>
        ))}
        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="county" style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>County</label>
          <select id="county" required value={form.county} onChange={set('county')} style={{ ...inputStyle, background: '#fff' }}>
            <option value="">Select your county</option>
            {COUNTIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        <button type="submit" disabled={loading}
          style={{ width: '100%', padding: '0.875rem', background: '#006B3F', color: '#fff', border: 'none', borderRadius: 6, fontSize: '1rem', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 44 }}>
          {loading ? 'Activating…' : 'Activate account'}
        </button>
      </form>
    </main>
  )
}
