import { Link } from 'react-router-dom'

export default function LandingHero() {
  return (
    <>
      <section className="landing-hero">
        <div className="landing-hero__grid">
          <div>
            <span className="landing-eyebrow">For every Form 2–4 learner</span>
            <h1 className="landing-hero__heading">
              Discover. Plan. Choose.
              <span className="landing-script">Succeed.</span>
            </h1>
          </div>
          <div className="landing-hero__side">
            <p>
              &quot;STEM or Arts?&quot; shouldn&apos;t be a coin flip. Answer a few honest
              questions about what you enjoy, and we&apos;ll show you which CBC pathway
              actually fits you — before you have to choose.
            </p>
            <div className="landing-hero__nav" aria-hidden="true">
              <span className="landing-navdot">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M15 6l-6 6 6 6" />
                </svg>
              </span>
              <span className="landing-navdot landing-navdot--fill">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M9 6l6 6-6 6" />
                </svg>
              </span>
              <span className="landing-hero__nav-label">Scroll &middot; explore</span>
            </div>
            <div className="landing-hero__ctas">
              <Link to="/register" className="mk-btn mk-btn-dark">
                Get Started
              </Link>
              <Link to="/pathways" className="mk-btn mk-btn-outline">
                See the pathways
              </Link>
            </div>
          </div>
        </div>
      </section>

      <div className="landing-wrap">
        <div className="landing-filmstrip">
          <figure>
            <img
              src="/img/chinga-boys.jpg"
              alt="Students at Chinga Boys High School, Nyeri County"
              loading="eager"
            />
            <figcaption>Chinga Boys High — Nyeri</figcaption>
          </figure>
          <figure>
            <img src="/img/kagumo-high.jpg" alt="Kagumo High School, Nyeri County" loading="lazy" />
            <figcaption>Kagumo High — Nyeri</figcaption>
          </figure>
          <figure>
            <img
              src="/img/mangu-students.jpg"
              alt="Students at Mang'u High School, Kiambu County"
              loading="lazy"
            />
            <figcaption>Mang&apos;u High — Kiambu</figcaption>
          </figure>
        </div>
      </div>
    </>
  )
}
