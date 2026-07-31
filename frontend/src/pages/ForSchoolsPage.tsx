import { Link } from 'react-router-dom'
import PublicNav from '../components/marketing/PublicNav'
import PublicFooter from '../components/marketing/PublicFooter'
import '../styles/marketing.css'

const SCHOOL_MAILTO = 'mailto:schools@smartashauri.app?subject=Smarta%20Shauri%20school%20rollout'

const WORKFLOW = [
  {
    tag: 'Step 1',
    title: 'Approve learner links',
    body: 'A school code creates a pending request. A school administrator approves or rejects the learner before staff access is enabled.',
  },
  {
    tag: 'Step 2',
    title: 'Assign counsellors',
    body: 'Assign approved learners individually or in a selected cohort, then monitor each counsellor’s active workload.',
  },
  {
    tag: 'Step 3',
    title: 'Configure offerings',
    body: 'Select the current subject combinations actually offered by the school. Learners can compare availability before planning.',
  },
  {
    tag: 'Step 4',
    title: 'Review learner plans',
    body: 'Counsellors review submitted plans, agree visible next steps and schedule follow-ups without leaving the product.',
  },
]

const OPERATIONS = [
  {
    title: 'Evidence visibility',
    body: 'See assessment completion, academic evidence and saved choices for approved learners.',
  },
  {
    title: 'Explicit attention reasons',
    body: 'Prioritise evidence gaps and due follow-ups without a predictive risk score.',
  },
  {
    title: 'Learner-controlled parent access',
    body: 'Parents see a learner only after that learner approves the relationship.',
  },
  {
    title: 'Individual PDF reports',
    body: 'Authorized staff can download an advisory learner report for review conversations.',
  },
  {
    title: 'Operational dashboard',
    body: 'Monitor pending links, assignments, evidence, plans, reviews and configured offerings.',
  },
  {
    title: 'Audited decisions',
    body: 'Membership, verification, review, offering and report actions are recorded for accountability.',
  },
]

const BOUNDARIES = [
  {
    title: 'Current project geography',
    body: "The project rollout is currently limited to Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua. This is a product boundary, not a Ministry pilot designation.",
  },
  {
    title: 'Advisory guidance',
    body: 'Interest alignment and reports support discussion. They do not predict success or determine placement.',
  },
  {
    title: 'Official selection stays official',
    body: 'Smarta Shauri does not submit Senior School choices. Learners still use the official Ministry selection service.',
  },
]

const FAQS = [
  {
    question: 'Can any learner join our school workspace with a code?',
    answer:
      'No. The code creates a pending link. A school administrator must approve it before staff can assign a counsellor or access school-side records.',
  },
  {
    question: 'Can staff see parent access or private notes?',
    answer:
      'Parent access remains learner-controlled. Confidential counsellor notes stay separate; only explicitly shared actions are visible to learners or approved parents.',
  },
  {
    question: 'Does the system make the final subject decision?',
    answer:
      'No. It brings evidence, interests, available combinations and agreed next steps together so a learner can make an explainable provisional choice.',
  },
  {
    question: 'Is this a national rollout?',
    answer:
      "No. The current project rollout covers Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua.",
  },
]

export default function ForSchoolsPage() {
  return (
    <div className="mk-for-schools-page">
      <PublicNav />

      <main id="main-content">
      <section className="mk-hero">
        <div className="mk-hero__grid">
          <div>
            <span className="mk-eyebrow">For rollout schools</span>
            <h1 className="mk-hero__heading" style={{ marginTop: '1rem' }}>
              One journey.
              <span className="mk-script"> Clear handoffs.</span>
            </h1>
          </div>
          <div className="mk-hero__side">
            <p>
              Run learner approval, counsellor assignment, evidence review and subject
              combination planning in one accountable five-county project workflow.
            </p>
            <div className="mk-hero__ctas">
              <a className="mk-btn mk-btn-dark" href={SCHOOL_MAILTO}>Discuss the rollout</a>
              <Link className="mk-btn mk-btn-outline" to="/how-it-works">See the learner journey</Link>
            </div>
          </div>
        </div>
      </section>

      <div className="mk-band mk-band--white">
        <section className="mk-section">
          <span className="mk-eyebrow">School workflow</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>
            From pending link to reviewed plan.
          </h2>
          <p className="mk-section__lede" style={{ marginTop: '1rem' }}>
            Each handoff has a named role, an explicit status and an auditable decision.
          </p>

          <div className="mk-pilot-workflow">
            {WORKFLOW.map(item => (
              <article className="mk-pricing-card" key={item.title}>
                <span className="mk-pricing-card__tag">{item.tag}</span>
                <h3 className="mk-pricing-card__name">{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="mk-band mk-band--green">
        <section className="mk-section">
          <span className="mk-eyebrow">What teams can operate</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>
            Practical pilot controls.
          </h2>
          <p className="mk-section__lede" style={{ marginTop: '1rem' }}>
            These capabilities are implemented in the current project and available through role-based dashboards.
          </p>

          <div className="mk-value-grid">
            {OPERATIONS.map(item => (
              <article className="mk-value-card" key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="mk-band mk-band--white">
        <section className="mk-section">
          <span className="mk-eyebrow">Pilot boundaries</span>
          <h2 className="mk-section__heading" style={{ marginTop: '0.75rem' }}>
            Clear about what this is.
          </h2>
          <div className="mk-value-grid">
            {BOUNDARIES.map(item => (
              <article className="mk-value-card" key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>

          <div className="mk-faq">
            {FAQS.map(faq => (
              <div className="mk-faq-item" key={faq.question}>
                <h3>{faq.question}</h3>
                <p>{faq.answer}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="mk-band mk-band--gold">
        <section className="mk-section">
          <div className="mk-cta-band mk-cta-band--gold">
            <span className="mk-eyebrow">Pilot conversation</span>
            <p className="mk-cta-band__heading">
              Bring an explainable workflow
              <span className="mk-script"> to your school.</span>
            </p>
            <p className="mk-cta-band__sub">
              Tell us how your school currently handles subject guidance and learner review.
            </p>
            <a className="mk-btn mk-btn-dark" href={SCHOOL_MAILTO}>Discuss the pilot</a>
          </div>
        </section>
      </div>

      </main>
      <PublicFooter />
    </div>
  )
}
