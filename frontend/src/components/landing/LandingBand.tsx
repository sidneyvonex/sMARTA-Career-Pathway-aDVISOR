import type { ReactElement } from 'react'

interface LandingBandProps {
  variant: 'dark' | 'quote'
  icon: ReactElement
  heading: string
}

export default function LandingBand({ variant, icon, heading }: LandingBandProps) {
  return (
    <div className={`landing-band landing-band--${variant}`}>
      {icon}
      <p className="landing-band__heading">{heading}</p>
    </div>
  )
}
