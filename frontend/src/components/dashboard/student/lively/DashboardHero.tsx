import { Link } from 'react-router-dom'
import Avatar from '../../../common/Avatar'
import { formatCounty } from '../../../../lib/format'

interface Props {
  firstName: string
  lastName?: string
  photoUrl?: string | null
  gradeLabel?: string
  county?: string | null
  nextAction: { title: string; href: string }
}

function StudentCharacter() {
  return (
    <svg className="lv-hero__art" viewBox="0 0 310 250" fill="none" aria-hidden="true">
      <circle cx="184" cy="124" r="104" fill="var(--color-primary-light)" fillOpacity=".16" />
      <path d="M63 224c31-24 66-35 103-35 43 0 82 12 119 35" stroke="var(--color-primary-light)" strokeOpacity=".28" strokeWidth="2" />
      <path d="M244 44l5 14 14 5-14 5-5 14-5-14-14-5 14-5 5-14z" fill="var(--color-accent)" />
      <path d="M54 74l3 8 8 3-8 3-3 8-3-8-8-3 8-3 3-8z" fill="var(--color-flame)" />

      <path d="M112 230c3-47 27-75 69-75 43 0 67 28 70 75H112z" fill="var(--color-primary-dark)" />
      <path d="M150 159l31 26 31-26 13 11-14 60h-61l-14-60 14-11z" fill="var(--color-primary)" />
      <path d="M164 157l17 28 17-28-17 13-17-13z" fill="var(--color-surface)" />
      <path d="M175 184h12l8 46h-28l8-46z" fill="var(--color-accent)" />

      <rect x="169" y="130" width="24" height="34" rx="10" fill="var(--avatar-skin-3)" />
      <ellipse cx="181" cy="111" rx="39" ry="46" fill="var(--avatar-skin-3)" />
      <path d="M143 106c-4-35 13-57 39-57 29 0 45 22 38 61-5-16-14-24-26-26-15 12-32 14-51 10v12z" fill="var(--avatar-hair)" />
      <circle cx="153" cy="99" r="12" fill="var(--avatar-hair)" />
      <circle cx="164" cy="87" r="13" fill="var(--avatar-hair)" />
      <circle cx="179" cy="81" r="14" fill="var(--avatar-hair)" />
      <circle cx="195" cy="84" r="13" fill="var(--avatar-hair)" />
      <circle cx="209" cy="94" r="12" fill="var(--avatar-hair)" />
      <circle cx="166" cy="111" r="2.3" fill="var(--color-text)" />
      <circle cx="196" cy="111" r="2.3" fill="var(--color-text)" />
      <path d="M171 129c6 7 15 7 21 0" stroke="var(--color-text)" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M181 114v8" stroke="var(--avatar-skin-shadow)" strokeWidth="2" strokeLinecap="round" />

      <path d="M117 195l43 4 2 31h-52l7-35z" fill="var(--color-flame)" />
      <path d="M121 190l42 4-3 8-42-4 3-8z" fill="var(--color-accent)" />
      <path d="M205 191l39-3 8 42h-50l3-39z" fill="var(--color-accent)" />
      <path d="M208 185l37-3 1 9-39 3 1-9z" fill="var(--color-surface)" />
      <path d="M153 199c8 1 15 8 14 15-1 8-7 12-15 11" fill="var(--avatar-skin-3)" />
      <path d="M211 192c-8 1-14 8-13 15 1 8 7 12 15 11" fill="var(--avatar-skin-3)" />
    </svg>
  )
}

export default function DashboardHero({
  firstName,
  lastName = '',
  photoUrl,
  gradeLabel,
  county,
  nextAction,
}: Props) {
  return (
    <section className="lv-hero" aria-labelledby="student-dashboard-title">
      <div className="lv-hero__landscape" aria-hidden="true" />
      <div className="lv-hero__content">
        <span className="lv-hero__eyebrow">
          <Avatar
            seed={`${firstName} ${lastName}`}
            photoUrl={photoUrl}
            size={38}
            shape="squircle"
            className="lv-hero__avatar"
          />
          Your journey
        </span>
        <h1 id="student-dashboard-title" className="lv-hero__title">
          Karibu, {firstName}
        </h1>
        <p className="lv-hero__sub">
          Your evidence and choices shape the next step. You can revisit every stage before review.
        </p>

        <div className="lv-hero__next">
          <span>Next action</span>
          <strong>{nextAction.title}</strong>
        </div>

        <div className="lv-hero__footer">
          <Link to={nextAction.href} className="lv-hero__cta">
            Continue
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </Link>
          <span className="lv-hero__meta">
            {[gradeLabel, formatCounty(county)].filter(Boolean).join(' · ')}
          </span>
        </div>
      </div>
      <StudentCharacter />
    </section>
  )
}
