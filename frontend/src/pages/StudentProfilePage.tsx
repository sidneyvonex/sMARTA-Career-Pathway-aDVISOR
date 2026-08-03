import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { studentsApi, StudentProfile } from '../api/students'
import ProfileForm from '../components/students/ProfileForm'
import PhotoUpload from '../components/students/PhotoUpload'
import Avatar from '../components/common/Avatar'
import { formatCounty } from '../lib/format'
import '../styles/student-pages.css'

export default function StudentProfilePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['student-profile'],
    queryFn: () => studentsApi.getProfile().then((response) => response.data.data),
  })
  const [profile, setProfile] = useState<StudentProfile | null>(null)

  if (isLoading) {
    return <div className="student-page-state" role="status" aria-live="polite">Loading your profile…</div>
  }

  if (isError || !data) {
    return <div className="student-page-state student-page-state--error" role="alert">We could not load your profile. Please try again.</div>
  }

  const current = profile ?? data
  const fullName = `${current.first_name} ${current.last_name}`
  const learningModeLabel = current.mode === 'self_guided'
    ? 'Self-guided'
    : current.school_membership_status === 'pending'
      ? 'School approval pending'
      : current.school_membership_status === 'rejected'
        ? 'School request declined'
        : 'School-linked'

  return (
    <div className="student-page student-page--profile">
      <header className="profile-hero">
        <div className="profile-hero__avatar">
          <Avatar seed={fullName} size={116} shape="squircle" />
        </div>
        <div className="profile-hero__copy">
          <span className="student-page__eyebrow">Your student identity</span>
          <h1>{fullName}</h1>
          <p>{current.email}</p>
          <div className="profile-hero__chips">
            <span>Grade {current.grade}</span>
            <span>{formatCounty(current.county) || 'County not set'}</span>
            <span>{learningModeLabel}</span>
          </div>
        </div>
        <div className="profile-hero__spark" aria-hidden="true">✦</div>
      </header>

      <div className="student-page__grid student-page__grid--profile">
        <section className="student-panel profile-photo-panel">
          <div className="student-panel__heading">
            <div>
              <span className="student-panel__kicker">Make it yours</span>
              <h2>Profile photo</h2>
            </div>
          </div>
          <p className="student-panel__intro">Add a photo so your counselor and school team can recognise you quickly.</p>
          <PhotoUpload
            photoUrl={current.photo_url}
            fallbackName={fullName}
            onUploaded={(url) => setProfile({ ...current, photo_url: url || null })}
          />

          <dl className="profile-facts">
            <div>
              <dt>Grade</dt>
              <dd>{current.grade}</dd>
            </div>
            <div>
              <dt>County</dt>
              <dd>{formatCounty(current.county) || 'Not set'}</dd>
            </div>
            <div>
              <dt>Learning mode</dt>
              <dd>{learningModeLabel}</dd>
            </div>
          </dl>
        </section>

        <section className="student-panel student-panel--workspace">
          <div className="student-panel__heading">
            <div>
              <span className="student-panel__kicker">Your story</span>
              <h2>About me</h2>
            </div>
            <span className="student-panel__mark" aria-hidden="true">✎</span>
          </div>
          <p className="student-panel__intro">Tell us what matters to you. This helps make your pathway guidance more personal.</p>
          <ProfileForm profile={current} onSaved={(updated) => setProfile(updated)} />
        </section>
      </div>
    </div>
  )
}
