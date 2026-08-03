import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { studentsApi, StudentProfile, type JourneyStatus } from '../../api/students'

interface Props {
  profile: StudentProfile
  onSaved: (updated: StudentProfile) => void
}

const JOURNEY_OPTIONS: { value: JourneyStatus; label: string }[] = [
  { value: 'not_selected', label: 'I have not selected a pathway yet' },
  { value: 'selected', label: 'I have already selected my pathway and subjects' },
  { value: 'currently_enrolled', label: 'I am currently studying my selected subjects' },
  { value: 'reconsidering', label: 'I am considering changing my selection' },
  { value: 'unsure', label: 'I am not sure' },
]

export default function ProfileForm({ profile, onSaved }: Props) {
  const [bio, setBio] = useState(profile.bio)
  const [dateOfBirth, setDateOfBirth] = useState(profile.date_of_birth ?? '')
  const [interests, setInterests] = useState(profile.career_interests)
  const [journeyStatus, setJourneyStatus] = useState<JourneyStatus>(profile.journey_status)

  const mutation = useMutation({
    mutationFn: () =>
      studentsApi.updateProfile({
        bio,
        date_of_birth: dateOfBirth || null,
        career_interests: interests,
        journey_status: journeyStatus,
      }),
    onSuccess: (response) => {
      toast.success('Profile saved.')
      onSaved(response.data.data)
    },
    onError: () => toast.error('Failed to save profile.'),
  })

  return (
    <form
      onSubmit={(event) => { event.preventDefault(); mutation.mutate() }}
      className="profile-form"
    >
      <div className="student-field">
        <label htmlFor="journey-status">Where are you in your Senior School journey?</label>
        <select
          id="journey-status"
          value={journeyStatus}
          onChange={(event) => setJourneyStatus(event.target.value as JourneyStatus)}
          className="student-field__control"
        >
          <option value="">Choose one…</option>
          {JOURNEY_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <small className="student-field__hint">
          If you have already chosen your pathway, we will focus on tracking your
          progress. The interest quiz stays optional for you.
        </small>
      </div>

      <div className="student-field">
        <div className="student-field__label-row">
          <label htmlFor="bio">Bio — a little about you</label>
          <small>{bio.length}/500</small>
        </div>
        <textarea
          id="bio"
          value={bio}
          onChange={(event) => setBio(event.target.value)}
          rows={5}
          maxLength={500}
          className="student-field__control"
          placeholder="What are you proud of? What are you working towards?"
        />
      </div>

      <div className="student-field">
        <label htmlFor="dob">Date of birth</label>
        <input
          id="dob"
          type="date"
          value={dateOfBirth}
          onChange={(event) => setDateOfBirth(event.target.value)}
          className="student-field__control"
        />
      </div>

      <div className="student-field">
        <div className="student-field__label-row">
          <label htmlFor="interests">Career interests</label>
          <small>{interests.length}/500</small>
        </div>
        <textarea
          id="interests"
          value={interests}
          onChange={(event) => setInterests(event.target.value)}
          rows={4}
          maxLength={500}
          className="student-field__control"
          placeholder="Examples: architecture, health, coding, teaching, music…"
        />
      </div>

      <button type="submit" disabled={mutation.isPending} className="student-action student-action--wide">
        {mutation.isPending ? 'Saving…' : 'Save profile'}
      </button>
    </form>
  )
}
