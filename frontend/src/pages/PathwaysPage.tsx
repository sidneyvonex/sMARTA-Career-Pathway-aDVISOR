import { Link } from 'react-router-dom'
import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import '../styles/marketing.css'

type PathwayDetail = {
  name: string
  interestChips: string[]
  description: string
  subjectGroups: { label: string; subjects: string[] }[]
  careers: string[]
  media: { src: string; alt: string }
  reverse?: boolean
}

const PATHWAYS: PathwayDetail[] = [
  {
    name: 'STEM',
    interestChips: ['Investigative · primary signal', 'Realistic · supporting signal'],
    description:
      "Science, Technology, Engineering & Mathematics — often worth exploring for students who enjoy investigating how things work and solving real-world technical problems.",
    subjectGroups: [
      { label: 'Pure Sciences', subjects: ['Biology', 'Chemistry', 'Physics', 'Mathematics'] },
      { label: 'Applied Sciences', subjects: ['Agriculture', 'Computer Science', 'Home Science'] },
      { label: 'Technical Studies', subjects: ['Aviation', 'Building', 'Electrical', 'Metal Work', 'Wood Work'] },
    ],
    careers: ['Software Engineer', 'Doctor', 'Civil Engineer', 'Agronomist', 'Pilot', 'Electrician'],
    media: { src: '/img/alliance-biology.jpg', alt: 'A biology class in session at Alliance High School, Kenya' },
  },
  {
    name: 'Social Sciences',
    interestChips: ['Social · primary signal', 'Enterprising · supporting signal'],
    description:
      'Languages, Humanities & Business — often worth exploring for students interested in law, economics, education, governance, languages, and human behaviour.',
    subjectGroups: [
      { label: 'Languages & Literature', subjects: ['English', 'Kiswahili', 'French', 'Arabic', 'German'] },
      { label: 'Humanities & Business', subjects: ['History & Citizenship', 'Geography', 'Business Studies', 'Religious Education'] },
    ],
    careers: ['Lawyer', 'Diplomat', 'Economist', 'Teacher', 'Journalist', 'Entrepreneur'],
    media: { src: '/img/kiambu-high.jpg', alt: 'The academic complex at Kiambu High School, Kiambu County' },
    reverse: true,
  },
  {
    name: 'Arts & Sports Science',
    interestChips: ['Artistic · primary signal', 'Realistic & Social · supporting signals'],
    description:
      'Creative Arts & Athletics — often worth exploring for students drawn to music, dance, theatre, fine arts, or sports coaching.',
    subjectGroups: [
      { label: 'Arts', subjects: ['Music & Dance', 'Theatre & Film', 'Fine Arts'] },
      { label: 'Sports', subjects: ['Sports & Recreation Science', 'Physical Education'] },
    ],
    careers: ['Musician', 'Graphic Designer', 'Actor', 'Coach', 'Physiotherapist', 'Professional Athlete'],
    media: { src: '/img/ahs-scouts.jpg', alt: 'Students on parade, an extracurricular activity, at Alliance High School, Kenya' },
  },
]

export default function PathwaysPage() {
  return (
    <div className="mk-pathways-page">
      <PublicNav />

      {/* HERO */}
      <section className="mk-hero">
        <div className="mk-hero__grid">
          <div>
            <span className="mk-eyebrow">The three pathways</span>
            <h1 className="mk-hero__heading" style={{ marginTop: '1rem' }}>
              STEM. Social Sciences.
              <span className="mk-script">Arts &amp; Sports.</span>
            </h1>
          </div>
          <div className="mk-hero__side">
            <p>
              Every CBC pathway leads somewhere different. Here&apos;s what&apos;s actually
              inside each one — subjects, strengths, and where they tend to lead.
            </p>
            <div className="mk-hero__ctas">
              <Link className="mk-btn mk-btn-dark" to="/register">Take the assessment</Link>
              <Link className="mk-btn mk-btn-outline" to="/how-it-works">How suggestions work</Link>
            </div>
          </div>
        </div>
      </section>

      {/* PATHWAY DETAILS */}
      <section className="mk-section" style={{ paddingTop: '0.5rem' }}>
        {PATHWAYS.map((pathway) => (
          <div
            className={`mk-pathway-detail${pathway.reverse ? ' mk-pathway-detail--reverse' : ''}`}
            key={pathway.name}
          >
            <div className="mk-pathway-detail__media">
              <img src={pathway.media.src} alt={pathway.media.alt} loading="lazy" />
            </div>
            <div className="mk-pathway-detail__body">
              <div className="mk-pathway-detail__fit">
                {pathway.interestChips.map((chip) => (
                  <span className="mk-fit-chip" key={chip}>{chip}</span>
                ))}
              </div>
              <h2 className="mk-pathway-detail__heading">{pathway.name}</h2>
              <p className="mk-pathway-detail__desc">{pathway.description}</p>
              <div className="mk-subject-groups">
                {pathway.subjectGroups.map((group) => (
                  <div key={group.label}>
                    <span className="mk-subject-group__label">{group.label}</span>
                    <div className="mk-subject-chips">
                      {group.subjects.map((subject) => (
                        <span className="mk-subject-chip" key={subject}>{subject}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div>
                <span className="mk-career-label">Where it can lead</span>
                <div className="mk-career-list">
                  {pathway.careers.map((career) => (
                    <span className="mk-career-chip" key={career}>{career}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}

        <p className="mk-disclaimer">
          Career examples are illustrative, not exhaustive — every pathway opens more doors than
          we can list here. Interest alignment is advisory: it does not predict success, determine
          placement, or replace discussion with a counsellor.
        </p>
      </section>

      {/* CTA */}
      <div className="mk-band-alt">
        <section className="mk-section">
          <div className="mk-cta-band">
            <span className="mk-eyebrow">Find out</span>
            <p className="mk-cta-band__heading">
              Not sure
              <span className="mk-script">which one is yours?</span>
            </p>
            <p className="mk-cta-band__sub">One free assessment. Three ranked pathways.</p>
            <Link className="mk-btn mk-btn-cream" to="/register">
              Take the free assessment
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
          </div>
        </section>
      </div>

      <PublicFooter />
    </div>
  )
}
