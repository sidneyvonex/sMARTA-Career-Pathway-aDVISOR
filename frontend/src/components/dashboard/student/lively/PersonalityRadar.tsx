import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { usePrefersReducedMotion } from '../../../../hooks/useCountUp'

/* Brand values mirror theme.css tokens (SVG fills can't read CSS vars reliably in recharts). */
const FOREST = 'var(--color-primary)'

export interface RadarDatum {
  label: string
  value: number // 0..100
}

export default function PersonalityRadar({ data }: { data: RadarDatum[] }) {
  const reduced = usePrefersReducedMotion()
  const summary = data.length
    ? `RIASEC interest profile: ${data.map((item) => `${item.label}, score ${item.value}`).join('; ')}.`
    : 'RIASEC interest profile: no assessment scores.'

  return (
    <figure role="img" aria-label={summary} style={{ width: '100%', height: 260 }}>
      <div aria-hidden="true" style={{ width: '100%', height: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="72%">
            <PolarGrid stroke="var(--color-divider)" />
            <PolarAngleAxis
              dataKey="label"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12, fontWeight: 600, fontFamily: 'Poppins, sans-serif' }}
            />
            <Radar
              dataKey="value"
              stroke={FOREST}
              fill={FOREST}
              fillOpacity={0.35}
              strokeWidth={2}
              isAnimationActive={!reduced}
              animationDuration={900}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}
