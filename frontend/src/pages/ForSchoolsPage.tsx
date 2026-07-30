import { Link } from 'react-router-dom'
import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import '../styles/marketing.css'

const SCHOOL_MAILTO = 'mailto:schools@smartashauri.app?subject=Smarta%20Shauri%20for%20our%20school'

const CHECK_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
    <path d="M20 6L9 17l-5-5" />
  </svg>
)

type PricingTier = {
  tag: string
  name: string
  price: string
  priceSub: string
  features: string[]
  highlight?: boolean
  badge?: string
  cta:
    | { kind: 'link'; label: string; to: string; variant: 'outline' | 'cream' }
    | { kind: 'mailto'; label: string; variant: 'outline' | 'cream' }
    | { kind: 'status'; label: string }
}

const TIERS: PricingTier[] = [
  {
    tag: 'For every student',
    name: 'Free',
    price: 'KES 0',
    priceSub: 'Forever — no card, no trial period',
    features: [
      'The full RIASEC interest assessment',
      'Ranked interest-aligned CBC pathways',
      'Subject & grade tracking every term',
      'Your own student dashboard',
    ],
    cta: { kind: 'link', label: 'Create your free account', to: '/register', variant: 'outline' },
  },
  {
    tag: 'For schools & counselors',
    name: 'School License',
    price: 'Custom quote',
    priceSub: 'Per-student annual license, priced by school size',
    features: [
      'Everything in Free, for every enrolled student',
      'Counselor panel with cohort-wide analytics',
      'Bulk PDF reports for every student',
      'School-wide parent notifications',
      'Priority support & onboarding',
    ],
    highlight: true,
    badge: 'Primary plan',
    cta: { kind: 'mailto', label: 'Talk to us about your school', variant: 'cream' },
  },
  {
    tag: 'For self-guided students',
    name: 'Individual Premium',
    price: 'Pricing TBD',
    priceSub: 'A small one-off fee per term, not a subscription',
    features: [
      'Everything in Free',
      'Downloadable, printable PDF reports',
      'Unlimited retakes with trend history',
      'Deeper career & labour-market content',
      'Parent progress digests',
    ],
    cta: { kind: 'status', label: 'In development' },
  },
]

const VALUES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path d="M12 3v18M5 8l7-5 7 5M5 8v8a2 2 0 002 2h10a2 2 0 002-2V8" />
      </svg>
    ),
    title: 'No price barrier for students',
    body: 'The assessment, interest-aligned pathway suggestions, and grade tracking stay free for every individual, indefinitely — that promise doesn’t change.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M8 2v4M16 2v4M3 10h18" />
      </svg>
    ),
    title: 'Schools already budget for this',
    body: 'A per-student license fits alongside the portals and services schools already pay for — it’s a familiar line item, not a new category of spend.',
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path d="M9 12l2 2 4-4M12 3l8 4v5c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V7l8-4z" />
      </svg>
    ),
    title: 'The free tier never gets crippled',
    body: 'Licensing pays for the analytics layer on top — not for unlocking features that were free yesterday.',
  },
]

const FAQS = [
  {
    question: 'Will the free tier ever start charging students?',
    answer:
      'No. The RIASEC assessment, interest-aligned pathway suggestions, and grade tracking stay free for every individual student, indefinitely — licensing only pays for the school-side analytics and reporting layer.',
  },
  {
    question: 'How is the school license priced?',
    answer:
      'We’re finalizing per-student pricing based on school size. Get in touch and we’ll work out a quote together — there’s no public price list yet.',
  },
  {
    question: 'What if our school hasn’t licensed Smarta Shauri yet?',
    answer:
      'Students can still register without a school code and use the entire Free plan as self-guided learners. A license adds the counselor-side tools on top — it doesn’t gate the basics.',
  },
  {
    question: 'Is there support for public schools or NGO-sponsored programs?',
    answer:
      'That’s the plan — we’d like sponsors to be able to cover school licenses for institutions that can’t pay directly. Reach out if that’s your situation; we’re still working out the details.',
  },
]

function PricingCTA({ cta }: { cta: PricingTier['cta'] }) {
  if (cta.kind === 'link') {
    return (
      <Link className={`mk-btn mk-btn-${cta.variant} mk-pricing-card__cta`} to={cta.to}>
        {cta.label}
      </Link>
    )
  }
  if (cta.kind === 'mailto') {
    return (
      <a className={`mk-btn mk-btn-${cta.variant} mk-pricing-card__cta`} href={SCHOOL_MAILTO}>
        {cta.label}
      </a>
    )
  }
  return <span className="mk-pricing-card__status">{cta.label}</span>
}

export default function ForSchoolsPage() {
  return (
    <div className="mk-for-schools-page">
      <PublicNav />

      {/* HERO */}
      <section className="mk-hero">
        <div className="mk-hero__grid">
          <div>
            <span className="mk-eyebrow">For schools &amp; counselors</span>
            <h1 className="mk-hero__heading" style={{ marginTop: '1rem' }}>
              Free for students.
              <span className="mk-script">Built for schools too.</span>
            </h1>
          </div>
          <div className="mk-hero__side">
            <p>
              Every student gets the full guidance experience for free, always. Schools that want
              cohort-wide insight, bulk reporting, and priority support can license the counselor
              tools that sit on top.
            </p>
            <div className="mk-hero__ctas">
              <a className="mk-btn mk-btn-dark" href={SCHOOL_MAILTO}>Talk to us about your school</a>
              <Link className="mk-btn mk-btn-outline" to="/register">Try it as a student</Link>
            </div>
          </div>
        </div>
      </section>

      {/* WHITE BAND: PRICING */}
      <div className="mk-band mk-band--white">
        <section className="mk-section">
          <span className="mk-eyebrow">Plans</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>
            One tool, three ways to use it.
          </h2>
          <p className="mk-section__lede" style={{ marginTop: '1rem' }}>
            The guidance itself is never behind a paywall. What&apos;s optional is the reporting
            and analytics layer built on top of it.
          </p>

          <div className="mk-pricing-grid">
            {TIERS.map((tier) => (
              <div
                className={`mk-pricing-card${tier.highlight ? ' mk-pricing-card--highlight' : ''}`}
                key={tier.name}
              >
                {tier.badge && <span className="mk-pricing-card__badge">{tier.badge}</span>}
                <span className="mk-pricing-card__tag">{tier.tag}</span>
                <h3 className="mk-pricing-card__name">{tier.name}</h3>
                <div>
                  <p className="mk-pricing-card__price">{tier.price}</p>
                  <p className="mk-pricing-card__price-sub">{tier.priceSub}</p>
                </div>
                <ul className="mk-pricing-card__features">
                  {tier.features.map((feature) => (
                    <li key={feature}>
                      {CHECK_ICON}
                      {feature}
                    </li>
                  ))}
                </ul>
                <PricingCTA cta={tier.cta} />
              </div>
            ))}
          </div>

          <p className="mk-pricing-note">
            No school code yet? Every student can still register and use the entire Free plan as a
            self-guided learner — the school code field is optional. See how pricing decisions were
            made on the <Link to="/about">About page</Link>.
          </p>
        </section>
      </div>

      {/* GREEN BAND: WHY THIS MODEL */}
      <div className="mk-band mk-band--green">
        <section className="mk-section">
          <span className="mk-eyebrow">Why it works this way</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>
            Schools pay
            <span className="mk-script" style={{ color: 'var(--color-accent)', display: 'inline' }}>
              so students don&apos;t have to.
            </span>
          </h2>
          <p className="mk-section__lede" style={{ marginTop: '1rem', color: 'rgba(251, 248, 239, 0.8)' }}>
            Most CBC students can&apos;t put a card number into a guidance tool — and shouldn&apos;t
            have to. Institutions already budget for portals and services like this one, so
            that&apos;s where the cost belongs.
          </p>

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
      </div>

      {/* WHITE BAND: FAQ */}
      <div className="mk-band mk-band--white">
        <section className="mk-section">
          <span className="mk-eyebrow">Questions schools ask</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>
            Before you get in touch.
          </h2>

          <div className="mk-faq">
            {FAQS.map((faq) => (
              <div className="mk-faq-item" key={faq.question}>
                <h3>{faq.question}</h3>
                <p>{faq.answer}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* GOLD BAND: CTA */}
      <div className="mk-band mk-band--gold">
        <section className="mk-section">
          <div className="mk-cta-band mk-cta-band--gold">
            <span className="mk-eyebrow">Let&apos;s talk</span>
            <p className="mk-cta-band__heading">
              Ready to bring Smarta Shauri
              <span className="mk-script">to your school?</span>
            </p>
            <p className="mk-cta-band__sub">No obligation — just a conversation about what your school needs.</p>
            <a className="mk-btn mk-btn-dark" href={SCHOOL_MAILTO}>
              Talk to us
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </a>
          </div>
        </section>
      </div>

      <PublicFooter />
    </div>
  )
}
