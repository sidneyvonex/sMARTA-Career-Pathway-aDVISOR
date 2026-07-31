/*
 * Illustrated character avatar — friendly, brand-palette, offline (inline SVG).
 * Deterministic: the same `seed` always yields the same character, so a given
 * person keeps one avatar. Decorative; real user photos can replace later.
 */
interface Props {
  seed: string
  size?: number
  className?: string
  photoUrl?: string | null
  shape?: 'circle' | 'squircle'
}

const BG = [
  'var(--avatar-bg-1)',
  'var(--avatar-bg-2)',
  'var(--avatar-bg-3)',
  'var(--avatar-bg-4)',
  'var(--avatar-bg-5)',
  'var(--avatar-bg-6)',
]
const RING = [
  'var(--color-primary)',
  'var(--color-accent-hover)',
  'var(--color-flame)',
  'var(--color-info)',
  'var(--color-purple)',
  'var(--avatar-teal)',
]
const SKIN = [
  'var(--avatar-skin-1)',
  'var(--avatar-skin-2)',
  'var(--avatar-skin-3)',
  'var(--avatar-skin-4)',
  'var(--avatar-skin-5)',
]
const HAIR = ['var(--avatar-hair)', 'var(--avatar-hair-2)', 'var(--avatar-hair-3)']
const SHIRT = [
  'var(--color-primary)',
  'var(--color-flame)',
  'var(--color-info)',
  'var(--color-purple)',
  'var(--avatar-teal)',
  'var(--color-accent-hover)',
]

function hash(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return h
}

export default function Avatar({
  seed,
  size = 44,
  className,
  photoUrl,
  shape = 'circle',
}: Props) {
  const h = hash(seed || 'x')
  const bg = BG[h % BG.length]
  const ring = RING[h % RING.length]
  const skin = SKIN[(h >> 3) % SKIN.length]
  const hair = HAIR[(h >> 5) % HAIR.length]
  const shirt = SHIRT[(h >> 7) % SHIRT.length]
  const hairStyle = h % 3 // 0 short, 1 rounded, 2 cropped

  const radius = shape === 'squircle' ? '30%' : '50%'

  if (photoUrl) {
    return (
      <img
        className={className}
        src={photoUrl}
        alt={`${seed} profile`}
        width={size}
        height={size}
        style={{
          width: size,
          height: size,
          borderRadius: radius,
          flexShrink: 0,
          display: 'block',
          objectFit: 'cover',
        }}
      />
    )
  }

  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label={`${seed} illustrated avatar`}
      style={{ borderRadius: radius, flexShrink: 0, display: 'block' }}
    >
      <circle cx="32" cy="32" r="32" fill={bg} />
      <circle cx="32" cy="32" r="31" fill="none" stroke={ring} strokeOpacity="0.25" strokeWidth="2" />
      {/* shoulders / shirt */}
      <path d="M14 60c0-10 8-16 18-16s18 6 18 16v4H14v-4z" fill={shirt} />
      {/* neck */}
      <rect x="28" y="34" width="8" height="10" rx="4" fill={skin} />
      {/* head */}
      <circle cx="32" cy="26" r="13" fill={skin} />
      {/* hair */}
      {hairStyle === 0 && <path d="M19 24c0-9 6-15 13-15s13 6 13 15c0-4-4-6-6-6-3 0-3 2-7 2s-4-2-7-2c-2 0-6 2-6 6z" fill={hair} />}
      {hairStyle === 1 && <path d="M18 25a14 14 0 0 1 28 0c0-3-2-4-3-6 0 2-2 3-3 2 0-2-1-4-3-4-1 2-4 2-5 0-2 0-3 2-3 4-1 1-3 0-3-2-1 2-3 3-3 6-1 0-2 0-2 0z" fill={hair} />}
      {hairStyle === 2 && <path d="M20 22c1-7 6-12 12-12s11 5 12 12c-2-3-5-4-12-4s-10 1-12 4z" fill={hair} />}
      {/* eyes */}
      <circle cx="27" cy="26" r="1.6" fill="var(--color-text)" />
      <circle cx="37" cy="26" r="1.6" fill="var(--color-text)" />
      {/* smile */}
      <path d="M28 31c1.5 2 6.5 2 8 0" stroke="var(--color-text)" strokeWidth="1.6" strokeLinecap="round" fill="none" />
    </svg>
  )
}
