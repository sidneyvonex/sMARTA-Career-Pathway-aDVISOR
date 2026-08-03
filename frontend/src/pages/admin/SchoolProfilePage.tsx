import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { schoolAdminApi } from '../../api/schoolAdmin'
import ManagementPage from '../../components/common/management/ManagementPage'
import EmptyState from '../../components/common/dashboard/EmptyState'
import { formatCounty } from '../../lib/format'
import '../../styles/school-admin.css'

export default function SchoolProfilePage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: school, isLoading, isError, refetch } = useQuery({
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

  function handleLogoSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) logoUploadMutation.mutate(file)
  }

  function handleSave() {
    if (!form) return
    updateMutation.mutate(form)
  }

  return (
    <ManagementPage
      eyebrow="School settings"
      title="School profile"
      description="Keep your school's identity and contact details current for learners, counsellors, and the guidance team."
      loading={isLoading}
      error={isError ? { title: 'The school profile could not load', description: 'Check your connection and try loading the school details again.' } : undefined}
      onRetry={() => refetch()}
      errorActionLabel="Retry school profile"
    >
      {!school ? (
        <EmptyState title="No school assigned" description="Your account is not linked to a school yet. Contact your system administrator." />
      ) : (
        <div className="school-profile-grid">
          <section className="school-profile-card">
            <span className="school-profile-card__kicker">Brand</span>
            <h2 className="school-profile-card__title">School logo</h2>
            <div className="school-profile-card__logo">
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
                  type="button"
                  className="btn-primary"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={logoUploadMutation.isPending}
                >
                  {logoUploadMutation.isPending ? 'Uploading…' : 'Upload logo'}
                </button>
                {school.logo_url && (
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => logoRemoveMutation.mutate()}
                    disabled={logoRemoveMutation.isPending}
                  >
                    Remove logo
                  </button>
                )}
              </div>
            </div>
            <p className="form-hint">Square PNG or JPEG works best. Shown to learners and on reports.</p>
          </section>

          <section className="school-profile-card">
            <span className="school-profile-card__kicker">Details</span>
            <h2 className="school-profile-card__title">School details</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleSave() }} className="school-profile-form">
              <div className="form-field">
                <label htmlFor="school-name">School name</label>
                <input
                  id="school-name"
                  type="text"
                  value={current.name}
                  onChange={(e) => setForm({ ...current, name: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-field">
                  <label htmlFor="school-code">School code</label>
                  <input
                    id="school-code"
                    type="text"
                    value={school.school_code ?? 'Not yet recorded'}
                    disabled
                  />
                  <p className="form-hint">Set by the system administrator.</p>
                </div>
                <div className="form-field">
                  <label htmlFor="school-county">County</label>
                  <input id="school-county" type="text" value={formatCounty(school.county)} disabled />
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
                    placeholder="+254…"
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
                <div className="school-profile-form__actions">
                  <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? 'Saving…' : 'Save changes'}
                  </button>
                  <button type="button" className="btn-ghost" onClick={() => setForm(null)}>
                    Cancel
                  </button>
                </div>
              )}
            </form>
          </section>
        </div>
      )}
    </ManagementPage>
  )
}
