export default function LandingPurpose() {
  return (
    <section className="landing-section">
      <span className="landing-eyebrow">Our work</span>
      <div className="landing-statement">
        <h2 className="landing-statement__heading">
          Three pathways.
          <span className="landing-script"> One decision.</span>
        </h2>
        <div className="landing-statement__side">
          <p className="landing-section__lede">
            You don&apos;t need to have it all figured out. CBC groups every subject choice
            into three broad pathways — we help you compare which options align with your
            interests and evidence, not just which one your friends picked.
          </p>
        </div>
      </div>

      <div className="landing-stat-row">
        <div className="landing-stat-card">
          <span className="landing-stat-card__label">CBC pathways</span>
          <span className="landing-stat-card__value">3</span>
          <p className="landing-stat-card__sub">STEM, Social Sciences, Arts &amp; Sports Science</p>
        </div>
        <div className="landing-stat-card">
          <span className="landing-stat-card__label">RIASEC dimensions</span>
          <span className="landing-stat-card__value">6</span>
          <p className="landing-stat-card__sub">Measured across a single interest assessment</p>
        </div>
        <div className="landing-stat-card">
          <span className="landing-stat-card__label">To get started</span>
          <span className="landing-stat-card__value">Free</span>
          <p className="landing-stat-card__sub">No cost, no credit card, ever</p>
        </div>
      </div>
    </section>
  )
}
