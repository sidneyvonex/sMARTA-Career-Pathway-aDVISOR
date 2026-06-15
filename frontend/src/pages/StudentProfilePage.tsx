import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { studentsApi, StudentProfile } from '../api/students'
import ProfileForm from '../components/students/ProfileForm'
import PhotoUpload from '../components/students/PhotoUpload'

export default function StudentProfilePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['student-profile'],
    queryFn: () => studentsApi.getProfile().then((r) => r.data.data),
  })
  const [profile, setProfile] = useState<StudentProfile | null>(null)

  if (isLoading) return <p style={{ padding: '2rem' }}>Loading…</p>
  if (isError || !data) return <p style={{ padding: '2rem', color: 'var(--color-error)' }}>Failed to load profile.</p>

  const current = profile ?? data

  return (
    <main style={{ maxWidth: '640px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontFamily: 'Inter, sans-serif', color: 'var(--color-text)', marginBottom: '1.5rem' }}>
        My Profile
      </h1>

      <section style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <p><strong>Name:</strong> {current.first_name} {current.last_name}</p>
        <p><strong>Email:</strong> {current.email}</p>
        <p><strong>County:</strong> {current.county}</p>
        <p><strong>Grade:</strong> {current.grade}</p>
        <p><strong>Mode:</strong> {current.mode === 'self_guided' ? 'Self-Guided' : 'School-Linked'}</p>
      </section>

      <section style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Profile Photo</h2>
        <PhotoUpload
          photoUrl={current.photo_url}
          onUploaded={(url) => setProfile({ ...current, photo_url: url || null })}
        />
      </section>

      <section style={{ background: 'var(--color-surface)', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>About Me</h2>
        <ProfileForm profile={current} onSaved={(updated) => setProfile(updated)} />
      </section>
    </main>
  )
}
