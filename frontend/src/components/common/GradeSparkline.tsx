import { GRADE_LEVEL_POINTS, type GradeLevel } from '../../api/students'

export interface GradeSparklineRecord {
  level: GradeLevel
}

const SPARK_WIDTH = 96
const SPARK_HEIGHT = 28
const SPARK_PAD_Y = 4

// GRADE_LEVEL_POINTS is an ordinal rank (1-8), never averaged: this plots each
// recorded level's own rank as a step, it does not interpolate between levels.
function sparkPoints(records: GradeSparklineRecord[]): { x: number; y: number }[] {
  if (records.length < 2) return []
  const usableHeight = SPARK_HEIGHT - SPARK_PAD_Y * 2
  return records.map((record, index) => ({
    x: (index / (records.length - 1)) * SPARK_WIDTH,
    y: SPARK_PAD_Y + usableHeight * (1 - (GRADE_LEVEL_POINTS[record.level] - 1) / 7),
  }))
}

function stepPath(points: { x: number; y: number }[]): string {
  return points
    .map((point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`
      const prev = points[index - 1]
      return `L ${point.x} ${prev.y} L ${point.x} ${point.y}`
    })
    .join(' ')
}

export default function GradeSparkline({ records }: { records: GradeSparklineRecord[] }) {
  const points = sparkPoints(records)
  if (points.length < 2) return null
  const last = points[points.length - 1]

  return (
    <svg
      className="grade-sparkline"
      viewBox={`0 0 ${SPARK_WIDTH} ${SPARK_HEIGHT}`}
      aria-hidden="true"
      focusable="false"
    >
      <path d={stepPath(points)} pathLength={1} />
      <circle cx={last.x} cy={last.y} r={2.5} />
    </svg>
  )
}
