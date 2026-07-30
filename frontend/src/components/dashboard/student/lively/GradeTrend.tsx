import { Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { usePrefersReducedMotion } from '../../../../hooks/useCountUp'

const FOREST = 'var(--color-primary)'
const MARIGOLD = 'var(--color-accent)'

export interface GradePoint {
  term: string
  score: number // e.g. average grade 0..100 or GPA-ish
}

export default function GradeTrend({ data }: { data: GradePoint[] }) {
  const reduced = usePrefersReducedMotion()
  return (
    <div style={{ width: '100%', height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 2, bottom: 0 }}>
          <defs>
            <linearGradient id="gradeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={MARIGOLD} stopOpacity={0.45} />
              <stop offset="100%" stopColor={MARIGOLD} stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-divider)" vertical={false} />
          <XAxis dataKey="term" tick={{ fill: 'var(--color-text-secondary)', fontSize: 11, fontFamily: 'DM Sans, sans-serif' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'var(--color-text-secondary)', fontSize: 11, fontFamily: 'DM Sans, sans-serif' }} axisLine={false} tickLine={false} width={38} domain={[0, 100]} />
          <Tooltip
            contentStyle={{ borderRadius: 12, border: '1px solid var(--color-divider)', fontFamily: 'DM Sans, sans-serif', fontSize: 12 }}
            formatter={(v) => [`${Math.round(Number(v))}%`, 'Average']}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke={FOREST}
            strokeWidth={2.5}
            fill="url(#gradeFill)"
            isAnimationActive={!reduced}
            animationDuration={900}
            dot={{ r: 3, fill: FOREST, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
