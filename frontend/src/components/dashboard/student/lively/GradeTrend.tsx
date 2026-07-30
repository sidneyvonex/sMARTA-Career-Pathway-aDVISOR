import { Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { usePrefersReducedMotion } from '../../../../hooks/useCountUp'

const FOREST = 'var(--color-primary)'
const MARIGOLD = 'var(--color-accent)'

export interface GradePoint {
  term: string
  points: number
}

const LEVEL_BY_POINTS: Record<number, string> = {
  1: 'BE2',
  2: 'BE1',
  3: 'AE2',
  4: 'AE1',
  5: 'ME2',
  6: 'ME1',
  7: 'EE2',
  8: 'EE1',
}

export default function GradeTrend({ data }: { data: GradePoint[] }) {
  const reduced = usePrefersReducedMotion()
  const summary = data.length
    ? `Academic trend: ${data.map((point) => `${point.term}, ${LEVEL_BY_POINTS[Math.round(point.points)] ?? point.points}`).join('; ')}.`
    : 'Academic trend: no recorded grade points.'

  return (
    <figure role="img" aria-label={summary} style={{ width: '100%', height: 220 }}>
      <div aria-hidden="true" style={{ width: '100%', height: '100%' }}>
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
            <YAxis
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 11, fontFamily: 'DM Sans, sans-serif' }}
              axisLine={false}
              tickLine={false}
              width={38}
              domain={[1, 8]}
              ticks={[1, 2, 3, 4, 5, 6, 7, 8]}
              tickFormatter={(value) => LEVEL_BY_POINTS[Number(value)]}
            />
            <Tooltip
              contentStyle={{ borderRadius: 12, border: '1px solid var(--color-divider)', fontFamily: 'DM Sans, sans-serif', fontSize: 12 }}
              formatter={(value) => [`${Number(value).toFixed(1)} / 8`, 'Average level']}
            />
            <Area
              type="monotone"
              dataKey="points"
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
    </figure>
  )
}
