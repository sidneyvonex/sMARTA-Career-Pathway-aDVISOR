# Subject Progress Card Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On the "My progress" page, minimize each subject card to a status badge + personalized teaser, and reveal a sparkline trend chart when the card is expanded.

**Architecture:** Extract the existing sparkline SVG renderer out of `GradeTrend.tsx` (lively dashboard) into a shared `components/common/GradeSparkline.tsx` component. Wire it into `ProgressSubjectCard.tsx`'s existing `detailsOpen` expand/collapse state: collapsed shows `suggested_action` as the teaser, expanded shows the sparkline + the existing trend sentence, explanation, and evidence tables (unchanged).

**Tech Stack:** React 18 + TypeScript, Vitest + React Testing Library + MSW 2, CSS variables (no new libraries).

## Global Constraints

- No backend/API changes — `suggested_action` and `records_used` already exist on `SubjectProgress` (`frontend/src/api/students.ts:149-164`).
- No hardcoded hex colors — use CSS variables (`CLAUDE.md` §3).
- Every form/interactive control keeps existing accessible names (`aria-expanded`, `aria-controls`, `aria-label`) — do not regress existing a11y wiring in `ProgressSubjectCard.tsx`.
- No change to "Manage subjects", filters, or the nested "View full evidence history" toggle behavior.

---

### Task 1: Extract `GradeSparkline` into a shared component

**Files:**
- Create: `frontend/src/components/common/GradeSparkline.tsx`
- Modify: `frontend/src/components/dashboard/student/lively/GradeTrend.tsx`
- Modify: `frontend/src/styles/dashboard-lively.css` (remove `.lv-grade-chronology__spark` rules, they move to theme.css)
- Modify: `frontend/src/styles/theme.css` (add shared `.grade-sparkline` rules)
- Test: `frontend/src/test/chart-accessibility.test.tsx` (existing test, must still pass unmodified — verifies extraction didn't change `GradeTrend`'s public behavior)

**Interfaces:**
- Produces: `frontend/src/components/common/GradeSparkline.tsx` exports:
  - `export interface GradeSparklineRecord { level: GradeLevel }`
  - `export default function GradeSparkline({ records }: { records: GradeSparklineRecord[] }): JSX.Element | null`
  - Renders `null` when `records.length < 2` (same as current behavior).
  - Root element: `<svg className="grade-sparkline" viewBox="0 0 96 28" aria-hidden="true" focusable="false">` containing a `<path>` and a `<circle>` — no other markup.
- Consumes: `GradeLevel` and `GRADE_LEVEL_POINTS` from `frontend/src/api/students.ts` (already exported, no change needed there).

- [ ] **Step 1: Write the failing test for the extracted component**

Create `frontend/src/test/grade-sparkline.test.tsx`:

```tsx
import { render } from '@testing-library/react'
import GradeSparkline from '../components/common/GradeSparkline'

describe('GradeSparkline', () => {
  it('renders a step-line svg for two or more records', () => {
    const { container } = render(
      <GradeSparkline records={[{ level: 'ME2' }, { level: 'EE2' }]} />,
    )
    const svg = container.querySelector('svg.grade-sparkline')
    expect(svg).toBeInTheDocument()
    expect(svg?.querySelector('path')).toBeInTheDocument()
    expect(svg?.querySelector('circle')).toBeInTheDocument()
  })

  it('renders nothing for fewer than two records', () => {
    const { container } = render(<GradeSparkline records={[{ level: 'ME2' }]} />)
    expect(container.querySelector('svg')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && npm test -- grade-sparkline`
Expected: FAIL — `Cannot find module '../components/common/GradeSparkline'`

- [ ] **Step 3: Create the shared component**

Create `frontend/src/components/common/GradeSparkline.tsx`:

```tsx
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd frontend && npm test -- grade-sparkline`
Expected: PASS (2 tests)

- [ ] **Step 5: Move the sparkline CSS rules to the shared stylesheet**

In `frontend/src/styles/dashboard-lively.css`, delete these rules (they move to theme.css):

```css
.lv-grade-chronology__spark {
  flex-shrink: 0;
  width: 6rem;
  height: 1.75rem;
  overflow: visible;
}

.lv-grade-chronology__spark path {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 1.75;
  stroke-linejoin: round;
}

.lv-grade-chronology__spark circle {
  fill: var(--color-accent);
}

@media (prefers-reduced-motion: no-preference) {
  .lv-grade-chronology__spark path {
    stroke-dasharray: 1;
    stroke-dashoffset: 1;
    animation: lv-spark-draw 0.6s ease-out forwards;
  }
}

@keyframes lv-spark-draw {
  to { stroke-dashoffset: 0; }
}
```

Leave `.lv-grade-chronology__heading` and every other `.lv-grade-chronology*` rule untouched.

Append to `frontend/src/styles/theme.css` (end of file):

```css
.grade-sparkline {
  flex-shrink: 0;
  width: 6rem;
  height: 1.75rem;
  overflow: visible;
}

.grade-sparkline path {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 1.75;
  stroke-linejoin: round;
}

.grade-sparkline circle {
  fill: var(--color-accent);
}

@media (prefers-reduced-motion: no-preference) {
  .grade-sparkline path {
    stroke-dasharray: 1;
    stroke-dashoffset: 1;
    animation: grade-sparkline-draw 0.6s ease-out forwards;
  }
}

@keyframes grade-sparkline-draw {
  to { stroke-dashoffset: 0; }
}
```

- [ ] **Step 6: Update `GradeTrend.tsx` to use the shared component**

Modify `frontend/src/components/dashboard/student/lively/GradeTrend.tsx`. Replace the whole file with:

```tsx
import GradeSparkline from '../../../common/GradeSparkline'
import { GRADE_LEVEL_LABELS, type GradeLevel } from '../../../../api/students'

export interface GradeChronologyRecord {
  period: string
  level: GradeLevel
}

export interface GradeChronology {
  subject: string
  records: GradeChronologyRecord[]
}

export default function GradeTrend({ data }: { data: GradeChronology[] }) {
  return (
    <section className="lv-grade-chronology" role="region" aria-label="Academic evidence chronology">
      <p>Levels are shown within each subject and term.</p>
      <ul>
        {data.map((subject) => (
          <li key={subject.subject}>
            <div className="lv-grade-chronology__heading">
              <strong>{subject.subject}</strong>
              <GradeSparkline records={subject.records} />
            </div>
            <div>
              {subject.records.map((record) => (
                <span
                  key={`${record.period}-${record.level}`}
                  title={GRADE_LEVEL_LABELS[record.level]}
                >
                  {record.period} · {record.level}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
```

- [ ] **Step 7: Run both the new and existing chart tests**

Run: `cd frontend && npm test -- grade-sparkline chart-accessibility`
Expected: PASS (all tests in both files, including the pre-existing `chart-accessibility.test.tsx` unmodified)

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/common/GradeSparkline.tsx frontend/src/components/dashboard/student/lively/GradeTrend.tsx frontend/src/styles/dashboard-lively.css frontend/src/styles/theme.css frontend/src/test/grade-sparkline.test.tsx
git commit -m "refactor(frontend): extract GradeSparkline into a shared component"
```

---

### Task 2: Minimize `ProgressSubjectCard` with a personalized teaser

**Files:**
- Modify: `frontend/src/components/students/ProgressSubjectCard.tsx`
- Modify: `frontend/src/styles/student-pages.css`
- Test: `frontend/src/test/academic-progress-page.test.tsx`

**Interfaces:**
- Consumes: `GradeSparkline` from `frontend/src/components/common/GradeSparkline.tsx` (Task 1) — `<GradeSparkline records={progress.records_used} />` (`ProgressEvidence` already has a `level: GradeLevel` field, so it structurally satisfies `GradeSparklineRecord[]` with no mapping).
- Produces: no exported changes — `ProgressSubjectCard`'s props (`Props` interface at line 32) are unchanged.

- [ ] **Step 1: Write the failing tests**

In `frontend/src/test/academic-progress-page.test.tsx`, replace the assertion block in the first test (`'summarises every readiness status with explainable evidence and an accessible trend table'`, currently lines 158-168) that checks the trend sentence is visible before expansion. Replace:

```tsx
    expect(screen.getByText(
      'Improving from Approaching Expectation - Level 2 to Meeting Expectation - Level 2 across 2 status records.',
    )).toBeInTheDocument()
    expect(screen.getByText('Mixed learner-entered and school-verified evidence')).toBeInTheDocument()
    expect(screen.queryByRole('table', {
      name: 'Mathematics evidence used for this status',
    })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'View Mathematics details' }))
    expect(screen.getAllByText('CBC-SENIOR-SCHOOL pilot-2026').length).toBeGreaterThan(0)
    expect(screen.queryByText('Rule: latest_ee_or_improving_to_me2_strong')).not.toBeInTheDocument()
    expect(screen.getByText('Review the next Mathematics learning activity.')).toBeInTheDocument()
```

with:

```tsx
    expect(screen.getByText('Review the next Mathematics learning activity.')).toBeInTheDocument()
    expect(screen.getByText('Mixed learner-entered and school-verified evidence')).toBeInTheDocument()
    expect(screen.queryByText(
      'Improving from Approaching Expectation - Level 2 to Meeting Expectation - Level 2 across 2 status records.',
    )).not.toBeInTheDocument()
    expect(screen.queryByRole('table', {
      name: 'Mathematics evidence used for this status',
    })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'View Mathematics details' }))
    expect(screen.getByText(
      'Improving from Approaching Expectation - Level 2 to Meeting Expectation - Level 2 across 2 status records.',
    )).toBeInTheDocument()
    expect(screen.getAllByText('CBC-SENIOR-SCHOOL pilot-2026').length).toBeGreaterThan(0)
    expect(screen.queryByText('Rule: latest_ee_or_improving_to_me2_strong')).not.toBeInTheDocument()
    expect(screen.getAllByText('Review the next Mathematics learning activity.')).toHaveLength(1)
```

Note the last line: once expanded, the collapsed teaser (`suggested_action`) is hidden and only the "Suggested action:" line inside the explanation panel remains, so the text still appears exactly once.

Also update the test `'keeps trend copy tied to the unfiltered winning-rule evidence'` (currently lines 217-256). Replace:

```tsx
    renderPage()
    expect(await screen.findByText(
      'Declining from Exceeding Expectation - Level 1 to Meeting Expectation - Level 1 across 2 status records.',
    )).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Academic grade'), '9')
    expect(screen.getByText(
      'Declining from Exceeding Expectation - Level 1 to Meeting Expectation - Level 1 across 2 status records.',
    )).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'View Mathematics details' }))
```

with:

```tsx
    renderPage()
    await screen.findByRole('heading', { name: 'Mathematics' })
    await user.click(screen.getByRole('button', { name: 'View Mathematics details' }))
    expect(screen.getByText(
      'Declining from Exceeding Expectation - Level 1 to Meeting Expectation - Level 1 across 2 status records.',
    )).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Academic grade'), '9')
    expect(screen.getByText(
      'Declining from Exceeding Expectation - Level 1 to Meeting Expectation - Level 1 across 2 status records.',
    )).toBeInTheDocument()
```

Add a new test after the first test in the `describe` block:

```tsx
  it('reveals a sparkline trend chart only once a subject card is expanded', async () => {
    server.use(http.get('/api/v1/students/progress/', () => progressResponse()))
    const user = userEvent.setup()

    renderPage()
    await screen.findByRole('heading', { name: 'Mathematics' })

    const mathCard = screen.getByRole('heading', { name: 'Mathematics' }).closest('article')!
    expect(within(mathCard).queryByRole('img', { hidden: true })).not.toBeInTheDocument()
    expect(mathCard.querySelector('svg.grade-sparkline')).not.toBeInTheDocument()

    await user.click(within(mathCard).getByRole('button', { name: 'View Mathematics details' }))
    expect(mathCard.querySelector('svg.grade-sparkline')).toBeInTheDocument()
  })
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && npm test -- academic-progress-page`
Expected: FAIL — teaser text not found before expansion; `svg.grade-sparkline` never rendered.

- [ ] **Step 3: Update `ProgressSubjectCard.tsx`**

In `frontend/src/components/students/ProgressSubjectCard.tsx`:

Add the import (alongside the existing imports at the top):

```tsx
import GradeSparkline from '../common/GradeSparkline'
```

Replace the always-visible trend paragraph:

```tsx
      <p className="progress-subject__trend">{trendText(progress)}</p>
```

with a teaser shown only while collapsed:

```tsx
      {!detailsOpen && (
        <p className="progress-subject__teaser">{progress.suggested_action}</p>
      )}
```

Inside the expanded content block (`{detailsOpen && (<div className="progress-subject__details-content" id={detailsId}>`), add the trend chart as the first child, before the `evidence.length > 0 && (...)` trail block:

```tsx
          <div className="progress-subject__trend-chart">
            <GradeSparkline records={progress.records_used} />
            <p className="progress-subject__trend">{trendText(progress)}</p>
          </div>

```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd frontend && npm test -- academic-progress-page`
Expected: PASS (all tests in the file)

- [ ] **Step 5: Add teaser and trend-chart CSS**

In `frontend/src/styles/student-pages.css`, replace the existing rule:

```css
.progress-subject__trend {
  color: var(--color-text);
  font-weight: var(--font-weight-semibold);
}
```

with:

```css
.progress-subject__teaser {
  color: var(--color-text);
  font-weight: var(--font-weight-semibold);
}

.progress-subject__trend-chart {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.progress-subject__trend {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
```

- [ ] **Step 6: Run the full frontend test suite**

Run: `cd frontend && npm test`
Expected: PASS (no regressions elsewhere)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/students/ProgressSubjectCard.tsx frontend/src/styles/student-pages.css frontend/src/test/academic-progress-page.test.tsx
git commit -m "feat(frontend): minimize subject progress cards with a trend preview on expand"
```

---

## Self-Review Notes

- **Spec coverage:** Minimized default state (teaser = `suggested_action`) → Task 2 Step 3. Click-to-preview sparkline on expand → Task 2 Step 3 + Task 1. Shared `GradeSparkline` extraction → Task 1. Test updates named in the spec's Testing section → Task 2 Step 1.
- **Type consistency:** `GradeSparklineRecord` (Task 1) has one field, `level: GradeLevel`; `ProgressEvidence` (used for `records_used`) is a superset, so it's passed directly with no adapter in Task 2 — confirmed structurally compatible, no mapping function invented.
- **No placeholders:** every step includes literal code/CSS to write and the exact commands to run.
