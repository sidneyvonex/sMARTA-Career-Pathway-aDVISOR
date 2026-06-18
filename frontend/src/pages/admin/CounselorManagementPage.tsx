import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi } from '../../api/schoolAdmin'
import '../../styles/school-admin.css'

export default function CounselorManagementPage() {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [removingId, setRemovingId] = useState<number | null>(null)

  const { data: counselors, isLoading } = useQuery({
    queryKey: ['school-admin', 'counselors'],
    queryFn: () => schoolAdminApi.getCounselors().then(r => r.data.data),
  })

  const addMutation = useMutation({
    mutationFn: (email: string) => schoolAdminApi.addCounselor(email),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      toast.success(res.data.message)
      setEmail('')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to add counselor.')
    },
  })

  const removeMutation = useMutation({
    mutationFn: (id: number) => schoolAdminApi.removeCounselor(id),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'counselors'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'students'] })
      toast.success(res.data.message)
      setRemovingId(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to remove counselor.')
      setRemovingId(null)
    },
  })

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    addMutation.mutate(email.trim())
  }

  function handleRemove(id: number) {
    if (removingId === id) {
      removeMutation.mutate(id)
    } else {
      setRemovingId(id)
    }
  }

  if (isLoading) return <p className="loading-text">Loading counselors…</p>

  return (
    <div className="counselor-management-page">
      <h1>Counselors</h1>

      <form onSubmit={handleAdd} className="counselor-management-page__add-form">
        <label htmlFor="counselor-email" className="sr-only">Counselor email</label>
        <input
          id="counselor-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Counselor email address"
          required
        />
        <button type="submit" className="btn-primary" disabled={addMutation.isPending}>
          {addMutation.isPending ? 'Adding…' : 'Add Counselor'}
        </button>
      </form>

      {counselors && counselors.length > 0 ? (
        <table className="counselor-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Students</th>
              <th>Joined</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {counselors.map((c) => (
              <tr key={c.id}>
                <td>{c.first_name} {c.last_name}</td>
                <td>{c.email}</td>
                <td>{c.student_count}</td>
                <td>{new Date(c.joined_at).toLocaleDateString()}</td>
                <td>
                  <button
                    className="btn-ghost"
                    onClick={() => handleRemove(c.id)}
                    disabled={removeMutation.isPending}
                    style={removingId === c.id ? { color: 'var(--color-error)' } : undefined}
                  >
                    {removingId === c.id ? 'Confirm Remove' : 'Remove'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ color: 'var(--color-text-secondary)' }}>No counselors at this school yet.</p>
      )}
    </div>
  )
}
