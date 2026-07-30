import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { usePrefersReducedMotion } from '../../../../hooks/useCountUp'

/* Brand values mirror theme.css tokens. */
const COLORS = ['var(--color-primary)', 'var(--color-accent)', 'var(--color-flame)']

export interface PathwaySlice {
  name: string
  value: number // fit %
}

export default function PathwayDonut({ data, topLabel, topValue }: { data: PathwaySlice[]; topLabel: string; topValue: number }) {
  const reduced = usePrefersReducedMotion()
  return (
    <div style={{ position: 'relative', width: '100%', height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="62%"
            outerRadius="90%"
            paddingAngle={3}
            startAngle={90}
            endAngle={-270}
            isAnimationActive={!reduced}
            animationDuration={900}
            stroke="none"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
        <span style={{ fontFamily: 'Poppins, sans-serif', fontWeight: 800, fontSize: '1.6rem', color: 'var(--color-text)', lineHeight: 1 }}>{topValue}%</span>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>{topLabel}</span>
      </div>
    </div>
  )
}
