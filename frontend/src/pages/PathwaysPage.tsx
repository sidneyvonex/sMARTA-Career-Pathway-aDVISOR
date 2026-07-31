import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import { guidanceApi, guidanceKeys } from '../api/guidance'
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
    interestChips: ['Investigative, primary signal', 'Realistic, supporting signal'],
    description:
      'Science, Technology, Engineering and Mathematics can be worth exploring for learners who enjoy investigating how things work and solving technical problems.',
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
    interestChips: ['Social, primary signal', 'Enterprising, supporting signal'],
    description:
      'Languages, Humanities and Business can be worth exploring for learners interested in law, economics, education, governance, languages and human behaviour.',
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
    interestChips: ['Artistic, primary signal', 'Realistic and Social, supporting signals'],
    description:
      'Creative Arts and Athletics can be worth exploring for learners drawn to music, dance, theatre, fine arts or sports coaching.',
    subjectGroups: [
      { label: 'Arts', subjects: ['Music & Dance', 'Theatre & Film', 'Fine Arts'] },
      { label: 'Sports', subjects: ['Sports & Recreation Science', 'Physical Education'] },
    ],
    careers: ['Musician', 'Graphic Designer', 'Actor', 'Coach', 'Physiotherapist', 'Professional Athlete'],
    media: { src: '/img/ahs-scouts.jpg', alt: 'Students on parade, an extracurricular activity, at Alliance High School, Kenya' },
  },
]

export default function PathwaysPage() {
  const catalogueQ = useQuery({
    queryKey: [...guidanceKeys.all, 'public-pathway-overview'],
    queryFn: async () => {
      const [frameworkResponse, pathwaysResponse] = await Promise.all([
        guidanceApi.getFramework(),
        guidanceApi.getPathways(),
      ])
      return {
        framework: frameworkResponse.data.data,
        pathways: pathwaysResponse.data.data,
      }
    },
  })

  return (
    <div className="mk-pathways-page">
      <PublicNav />

      <main id="main-content">
      {/* HERO */}
      <section className="mk-hero">
        <div className="mk-hero__grid">
          <div>
            <span className="mk-eyebrow">The three pathways</span>
            <h1 className="mk-hero__heading" style={{ marginTop: '1rem' }}>
              STEM. Social Sciences.
              <span className="mk-script"> Arts &amp; Sports.</span>
            </h1>
          </div>
          <div className="mk-hero__side">
            <p>
              Explore current pathway tracks, illustrative subjects and possible directions
              in the project&apos;s five-county rollout.
            </p>
            <div className="mk-hero__ctas">
              <Link className="mk-btn mk-btn-dark" to="/register">Take the assessment</Link>
              <Link className="mk-btn mk-btn-outline" to="/how-it-works">How suggestions work</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mk-section mk-section--tight" aria-labelledby="current-catalogue-title">
        <div className="mk-catalogue-provenance">
          <div>
            <span className="mk-eyebrow">Current curated catalogue</span>
            <h2 id="current-catalogue-title">
              {catalogueQ.data?.framework.title ?? 'Loading current framework'}
            </h2>
            {catalogueQ.data?.framework ? (
              <p>
                <strong>{catalogueQ.data.framework.code}</strong>
                {' '}is effective from{' '}
                {new Date(`${catalogueQ.data.framework.effective_date}T00:00:00`).toLocaleDateString('en-KE', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}.
              </p>
            ) : catalogueQ.isError ? (
              <p>Current source metadata is temporarily unavailable. The pathway overview remains advisory.</p>
            ) : (
              <p>Checking the current source and effective date.</p>
            )}
          </div>
          {catalogueQ.data?.framework && (
            <a
              className="mk-btn mk-btn-outline"
              href={catalogueQ.data.framework.source_url}
              target="_blank"
              rel="noreferrer"
            >
              Open current official catalogue
            </a>
          )}
        </div>

        {catalogueQ.data?.pathways && (
          <div className="mk-current-track-grid">
            {catalogueQ.data.pathways.map(pathway => (
              <article key={pathway.id}>
                <h3>{pathway.name}</h3>
                <ul>
                  {pathway.tracks.map(track => (
                    <li key={track.id}>{track.name}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
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
          Subject and career examples are illustrative, not exhaustive. The source-dated catalogue
          above controls the combinations shown in the product. Interest alignment is advisory: it
          does not predict success, determine placement or replace discussion with a counsellor.
        </p>
      </section>

      {/* CTA */}
      <div className="mk-band-alt">
        <section className="mk-section">
          <div className="mk-cta-band">
            <span className="mk-eyebrow">Find out</span>
            <p className="mk-cta-band__heading">
              Not sure
              <span className="mk-script"> what to explore next?</span>
            </p>
            <p className="mk-cta-band__sub">
              One free assessment. Three pathways ranked by interest alignment.
            </p>
            <Link className="mk-btn mk-btn-cream" to="/register">
              Take the free assessment
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
          </div>
        </section>
      </div>

      </main>
      <PublicFooter />
    </div>
  )
}
