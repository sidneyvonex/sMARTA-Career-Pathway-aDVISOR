const TICKER_TEXT = 'Discover • Plan • Choose • Succeed • '

export default function LandingTicker() {
  return (
    <div className="landing-ticker" aria-hidden="true">
      <span className="landing-ticker__track">{TICKER_TEXT.repeat(4)}</span>
    </div>
  )
}
