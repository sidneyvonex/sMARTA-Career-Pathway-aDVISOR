interface IconProps {
  className?: string
}

export function CompassIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="24" cy="24" r="20" />
      <path d="M31 17l-5 11-11 5 5-11 11-5z" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function LightbulbIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M24 4a14 14 0 00-8 25.5V33a3 3 0 003 3h10a3 3 0 003-3v-3.5A14 14 0 0024 4z" />
      <line x1="19" y1="40" x2="29" y2="40" />
      <line x1="20" y1="44" x2="28" y2="44" />
    </svg>
  )
}

export function NetworkIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="24" cy="8" r="4" />
      <circle cx="8" cy="36" r="4" />
      <circle cx="40" cy="36" r="4" />
      <line x1="24" y1="12" x2="10" y2="33" />
      <line x1="24" y1="12" x2="38" y2="33" />
      <line x1="12" y1="36" x2="36" y2="36" />
    </svg>
  )
}

export function RoadmapIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M6 40C14 20 20 44 24 24S34 4 42 8" strokeLinecap="round" />
      <circle cx="6" cy="40" r="2.5" fill="currentColor" stroke="none" />
      <circle cx="42" cy="8" r="2.5" fill="currentColor" stroke="none" />
    </svg>
  )
}
