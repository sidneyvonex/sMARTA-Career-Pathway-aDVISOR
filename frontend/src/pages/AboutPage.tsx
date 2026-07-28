import { Link } from 'react-router-dom'
import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import '../styles/marketing.css'

const TIMELINE = [
  {
    label: 'Foundations',
    title: 'Accounts you can trust',
    body: 'Started with the basics that had to be right first: secure accounts, county-verified registration, and role-based access for students, parents, counselors, and school admins.',
  },
  {
    label: 'The core',
    title: 'Grades and the RIASEC engine',
    body: 'Built CBC grade tracking and the RIASEC interest assessment — the two pieces every other feature depends on.',
  },
  {
    label: 'The full picture',
    title: "Guidance isn't a one-person job",
    body: 'Added notifications, dashboards, a counselor panel, school admin tools, and parent access, so support can come from more than one direction.',
  },
  {
    label: 'Getting it ready',
    title: 'Reports and offline support',
    body: 'System administration, PDF reports, and offline-friendly PWA support, so it holds up outside a perfect Wi-Fi connection.',
  },
  {
    label: 'Now',
    title: 'Still building',
    body: 'Actively in development — this redesign is part of the next round.',
  },
]

const VALUES = [
  {
    title: 'No fabricated numbers',
    body: "Every stat on this site is real. If we don't have the data, we don't show a number — we say so.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path d="M9 12l2 2 4-4M12 3l8 4v5c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V7l8-4z" />
      </svg>
    ),
  },
  {
    title: 'No pay-to-recommend',
    body: 'Pathway matches come from your RIASEC score, not from anyone paying for placement.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path d="M12 3v18M5 8l7-5 7 5M5 8v8a2 2 0 002 2h10a2 2 0 002-2V8" />
      </svg>
    ),
  },
  {
    title: 'Built around CBC, not bolted on',
    body: "The pathways, subjects, and grading structure come straight from Kenya's Competency-Based Curriculum.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path d="M4 19.5A2.5 2.5 0 016.5 17H20M4 19.5A2.5 2.5 0 006.5 22H20V2H6.5A2.5 2.5 0 004 4.5v15z" />
      </svg>
    ),
  },
]

export default function AboutPage() {
  return (
    <div className="mk-about-page">
      <PublicNav />

      {/* HERO */}
      <section className="mk-hero">
        <div className="mk-hero__grid">
          <div>
            <span className="mk-eyebrow">Our story</span>
            <h1 className="mk-hero__heading" style={{ marginTop: '1rem' }}>
              Every learner deserves
              <span className="mk-script">a real answer.</span>
            </h1>
          </div>
          <div className="mk-hero__side">
            <p>
              Smarta Shauri started with one frustrating form: the CBC subject selection sheet.
              Too many students filled it in based on what a friend picked, or what a parent
              insisted on — not what actually fit them. We built something better.
            </p>
            <div className="mk-hero__ctas">
              <Link className="mk-btn mk-btn-dark" to="/register">Get Started</Link>
              <Link className="mk-btn mk-btn-outline" to="/how-it-works">See how it works</Link>
            </div>
          </div>
        </div>
      </section>

      {/* FILMSTRIP */}
      <div className="mk-wrap">
        <div className="mk-filmstrip">
          <figure>
            <img src="/img/kagumo-high.jpg" alt="Kagumo High School, Nyeri County" loading="eager" />
            <figcaption>Kagumo High School</figcaption>
          </figure>
          <figure>
            <img src="/img/ahs-scouts.jpg" alt="Scouts parade at Alliance High School, Kenya" loading="lazy" />
            <figcaption>Alliance High School</figcaption>
          </figure>
          <figure>
            <img src="/img/chinga-boys.jpg" alt="Students at Chinga Boys High School, Kenya" loading="lazy" />
            <figcaption>Chinga Boys High School</figcaption>
          </figure>
        </div>
      </div>

      {/* THE PROBLEM */}
      <section className="mk-section">
        <span className="mk-eyebrow">The problem</span>
        <div className="mk-statement">
          <h2 className="mk-statement__heading">
            Guesswork
            <span className="mk-script">isn&apos;t a plan.</span>
          </h2>
          <div className="mk-statement__side">
            <p className="mk-section__lede">
              Kenya&apos;s CBC opens up three broad pathways in Senior School — STEM, Social
              Sciences, and Arts &amp; Sports Science. Most students choose without ever measuring
              what they actually enjoy or where their strengths lie. We think that&apos;s backwards.
            </p>
          </div>
        </div>
      </section>

      {/* TIMELINE */}
      <div className="mk-band-alt">
        <section className="mk-section mk-section--tight">
          <span className="mk-eyebrow">How we got here</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>Built sprint by sprint.</h2>

          <div className="mk-timeline">
            {TIMELINE.map((item) => (
              <div className="mk-timeline-item" key={item.title}>
                <span className="mk-timeline-item__label">{item.label}</span>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* VALUES */}
      <section className="mk-section mk-section--tight">
        <span className="mk-eyebrow">What we won&apos;t do</span>
        <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>Three lines we don&apos;t cross.</h2>

        <div className="mk-value-grid">
          {VALUES.map((value) => (
            <div className="mk-value-card" key={value.title}>
              <span className="mk-value-card__icon">{value.icon}</span>
              <h3>{value.title}</h3>
              <p>{value.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="mk-band-alt">
        <section className="mk-section">
          <div className="mk-cta-band">
            <span className="mk-eyebrow">Try it now</span>
            <p className="mk-cta-band__heading">
              Curious what this
              <span className="mk-script">actually feels like?</span>
            </p>
            <p className="mk-cta-band__sub">Free forever. Takes about 15 minutes.</p>
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
