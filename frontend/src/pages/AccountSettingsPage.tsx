import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import '../styles/auth.css'

export default function AccountSettingsPage() {
  const { user, setUser } = useAuthStore()
  const queryClient = useQueryClient()

  const [firstName, setFirstName] = useState(user?.first_name ?? '')
  const [lastName, setLastName] = useState(user?.last_name ?? '')

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmError, setConfirmError] = useState('')

  const nameMutation = useMutation({
    mutationFn: () => authApi.updateMe({ first_name: firstName, last_name: lastName }),
    onSuccess: (response) => {
      setUser(response.data.data.user)
      queryClient.invalidateQueries({ queryKey: ['me'] })
      toast.success('Profile updated.')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Something went wrong. Please try again.')
    },
  })

  const passwordMutation = useMutation({
    mutationFn: () => authApi.changePassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      toast.success('Password updated.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Something went wrong. Please try again.')
    },
  })

  function handleNameSubmit(event: React.FormEvent) {
    event.preventDefault()
    nameMutation.mutate()
  }

  function handlePasswordSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (newPassword !== confirmPassword) {
      setConfirmError('Passwords do not match.')
      return
    }
    setConfirmError('')
    passwordMutation.mutate()
  }

  return (
    <div className="account-settings-page">
      <section className="auth-card">
        <h1 className="auth-heading">Your name</h1>
        <form onSubmit={handleNameSubmit} className="auth-form">
          <div className="form-field">
            <label htmlFor="account-first-name">First name</label>
            <input id="account-first-name" value={firstName} onChange={e => setFirstName(e.target.value)} required />
          </div>
          <div className="form-field">
            <label htmlFor="account-last-name">Last name</label>
            <input id="account-last-name" value={lastName} onChange={e => setLastName(e.target.value)} required />
          </div>
          <button type="submit" className="btn-primary" disabled={nameMutation.isPending}>
            {nameMutation.isPending ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </section>

      <section className="auth-card">
        <h2 className="account-settings-page__heading">Change password</h2>
        <form onSubmit={handlePasswordSubmit} className="auth-form">
          <div className="form-field">
            <label htmlFor="account-current-password">Current password</label>
            <input id="account-current-password" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required />
          </div>
          <div className="form-field">
            <label htmlFor="account-new-password">New password</label>
            <input id="account-new-password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required />
          </div>
          <div className="form-field">
            <label htmlFor="account-confirm-password">Confirm new password</label>
            <input id="account-confirm-password" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
          </div>
          {confirmError && <p className="auth-status error">{confirmError}</p>}
          <button type="submit" className="btn-primary" disabled={passwordMutation.isPending}>
            {passwordMutation.isPending ? 'Updating…' : 'Update password'}
          </button>
        </form>
      </section>
    </div>
  )
}
