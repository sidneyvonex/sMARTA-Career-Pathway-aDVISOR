import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi, StudentProfile } from '../../api/students'

interface Props {
  profile: StudentProfile
  onSaved: (updated: StudentProfile) => void
}

export default function ProfileForm({ profile, onSaved }: Props) {
  const [bio, setBio] = useState(profile.bio)
  const [dob, setDob] = useState(profile.date_of_birth ?? '')
  const [interests, setInterests] = useState(profile.career_interests)

  const mutation = useMutation({
    mutationFn: () =>
      studentsApi.updateProfile({
        bio,
        date_of_birth: dob || null,
        career_interests: interests,
      }),
    onSuccess: (res) => {
      toast.success('Profile saved.')
      onSaved(res.data.data)
    },
    onError: () => toast.error('Failed to save profile.'),
  })

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
      style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '480px' }}
    >
      <div>
        <label htmlFor="bio" style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}>
          Bio
        </label>
        <textarea
          id="bio"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={4}
          maxLength={500}
          style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}
        />
        <small style={{ color: 'var(--color-text-secondary)' }}>{bio.length}/500</small>
      </div>

      <div>
        <label htmlFor="dob" style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}>
          Date of Birth
        </label>
        <input
          id="dob"
          type="date"
          value={dob}
          onChange={(e) => setDob(e.target.value)}
          style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}
        />
      </div>

      <div>
        <label htmlFor="interests" style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}>
          Career Interests
        </label>
        <textarea
          id="interests"
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          rows={3}
          maxLength={500}
          style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--color-border)' }}
        />
        <small style={{ color: 'var(--color-text-secondary)' }}>{interests.length}/500</small>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        style={{ padding: '0.75rem', background: 'var(--color-primary)', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
      >
        {mutation.isPending ? 'Saving…' : 'Save Profile'}
      </button>
    </form>
  )
}
