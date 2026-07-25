import { Link } from 'react-router-dom'

export const PATHWAYS = [
  {
    name: 'STEM',
    blurb: 'Science, Technology, Engineering & Mathematics — for learners who love investigating how things work.',
  },
  {
    name: 'Social Sciences',
    blurb: 'Languages, Humanities & Business — for learners drawn to law, economics, governance, and human behaviour.',
  },
  {
    name: 'Arts & Sports Science',
    blurb: 'Creative Arts & Athletics — for learners drawn to music, art, theatre, or sports.',
  },
]

export default function LandingPathwayGrid() {
  return (
    <section className="landing-section">
      <h2 className="landing-section__heading">Explore Your Pathway</h2>
      <div className="landing-pathway-grid">
        {PATHWAYS.map((pathway) => (
          <article className="landing-pathway-card" key={pathway.name}>
            <h3>{pathway.name}</h3>
            <p>{pathway.blurb}</p>
          </article>
        ))}
        <article className="landing-pathway-card landing-pathway-card--cta">
          <p>Not sure yet?</p>
          <Link to="/register">Take the RIASEC Assessment &rarr;</Link>
        </article>
      </div>
    </section>
  )
}
