import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi, SchoolProfile } from '../../api/schoolAdmin'
import '../../styles/school-admin.css'

export default function SchoolProfilePage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: school, isLoading } = useQuery({
    queryKey: ['school-admin', 'school'],
    queryFn: () => schoolAdminApi.getSchool().then(r => r.data.data),
  })

  const [form, setForm] = useState<{ name: string; phone: string; email: string } | null>(null)

  const editing = form !== null
  const current = form ?? { name: school?.name ?? '', phone: school?.phone ?? '', email: school?.email ?? '' }

  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; phone?: string; email?: string }) =>
      schoolAdminApi.updateSchool(data),
    onSuccess: (res) => {
      queryClient.setQueryData(['school-admin', 'school'], res.data.data)
      toast.success('Profile updated.')
      setForm(null)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to update profile.')
    },
  })

  const logoUploadMutation = useMutation({
    mutationFn: (file: File) => schoolAdminApi.uploadLogo(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'school'] })
      toast.success('Logo updated.')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message ?? 'Failed to upload logo.')
    },
  })

  const logoRemoveMutation = useMutation({
    mutationFn: () => schoolAdminApi.removeLogo(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-admin', 'school'] })
      toast.success('Logo removed.')
    },
    onError: () => {
      toast.error('Failed to remove logo.')
    },
  })

  if (isLoading) return <p className="loading-text">Loading school profile...</p>
  if (!school) return <p>No school assigned to your account.</p>

  function handleLogoSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) logoUploadMutation.mutate(file)
  }

  function handleSave() {
    if (!form) return
    updateMutation.mutate(form)
  }

  return (
    <div className="school-profile-page">
      <h1>School Profile</h1>

      <div className="school-profile-page__logo-section">
        {school.logo_url ? (
          <img src={school.logo_url} alt="School logo" className="school-profile-page__logo-preview" />
        ) : (
          <div className="school-profile-page__logo-placeholder">No logo</div>
        )}
        <div className="school-profile-page__logo-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg"
            style={{ display: 'none' }}
            onChange={handleLogoSelect}
          />
          <button
            className="btn-primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={logoUploadMutation.isPending}
          >
            {logoUploadMutation.isPending ? 'Uploading...' : 'Upload Logo'}
          </button>
          {school.logo_url && (
            <button
              className="btn-ghost"
              onClick={() => logoRemoveMutation.mutate()}
              disabled={logoRemoveMutation.isPending}
            >
              Remove Logo
            </button>
          )}
        </div>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleSave() }} className="auth-form">
        <div className="form-field">
          <label htmlFor="school-name">School Name</label>
          <input
            id="school-name"
            type="text"
            value={current.name}
            onChange={(e) => setForm({ ...current, name: e.target.value })}
          />
        </div>

        <div className="form-row">
          <div className="form-field">
            <label htmlFor="school-code">School Code</label>
            <input id="school-code" type="text" value={school.school_code} disabled />
            <p className="form-hint">Set by the system administrator.</p>
          </div>
          <div className="form-field">
            <label htmlFor="school-county">County</label>
            <input id="school-county" type="text" value={school.county} disabled />
          </div>
        </div>

        <div className="form-row">
          <div className="form-field">
            <label htmlFor="school-phone">Phone</label>
            <input
              id="school-phone"
              type="tel"
              value={current.phone}
              onChange={(e) => setForm({ ...current, phone: e.target.value })}
              placeholder="+254..."
            />
          </div>
          <div className="form-field">
            <label htmlFor="school-email">Email</label>
            <input
              id="school-email"
              type="email"
              value={current.email}
              onChange={(e) => setForm({ ...current, email: e.target.value })}
              placeholder="info@school.ac.ke"
            />
          </div>
        </div>

        {editing && (
          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
            <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
            <button type="button" className="btn-ghost" onClick={() => setForm(null)}>
              Cancel
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
