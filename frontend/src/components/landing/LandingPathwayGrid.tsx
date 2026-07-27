import { Link } from 'react-router-dom'

export const PATHWAYS = [
  {
    name: 'STEM',
    pill: 'STEM',
    image: '/img/alliance-biology.jpg',
    alt: 'A biology class in session at Alliance High School, Kiambu County',
    blurb: 'Science, Technology, Engineering & Mathematics — for learners who love investigating how things work.',
  },
  {
    name: 'Social Sciences',
    pill: 'Social Sciences',
    image: '/img/kiambu-high.jpg',
    alt: 'The academic complex at Kiambu High School, Kiambu County',
    blurb: 'Languages, Humanities & Business — for learners drawn to law, economics, governance, and human behaviour.',
  },
  {
    name: 'Arts & Sports Science',
    pill: 'Arts & Sports',
    image: '/img/ahs-scouts.jpg',
    alt: 'Students on parade, an extracurricular activity, at Alliance High School, Kiambu County',
    blurb: 'Creative Arts & Athletics — for learners drawn to music, art, theatre, or sports.',
  },
]

export default function LandingPathwayGrid() {
  return (
    <section className="landing-section" id="pathways">
      <span className="landing-eyebrow">Explore your pathway</span>
      <h2 className="landing-section__heading" style={{ marginTop: '0.75rem' }}>
        Pick where you&apos;re headed.
      </h2>

      <div className="landing-pathway-grid">
        {PATHWAYS.map((pathway) => (
          <article className="landing-pathway-card" key={pathway.name}>
            <div className="landing-pathway-card__media">
              <span className="landing-pathway-card__pill">{pathway.pill}</span>
              <img src={pathway.image} alt={pathway.alt} loading="lazy" />
            </div>
            <div className="landing-pathway-card__body">
              <h3>{pathway.name}</h3>
              <p>{pathway.blurb}</p>
            </div>
          </article>
        ))}
      </div>

      <div className="landing-not-sure">
        <p>Not sure yet?</p>
        <Link to="/register">Take the RIASEC Assessment &rarr;</Link>
      </div>
    </section>
  )
}
