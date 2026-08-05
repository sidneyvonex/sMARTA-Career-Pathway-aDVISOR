# Subject Progress Card: Minimize + Click-to-Preview Trend

Date: 2026-08-05
Page: `frontend/src/components/students/AcademicProgressDashboard.tsx` → `ProgressSubjectCard.tsx`

## Problem

The "Subject progress" section renders one card per subject, each always showing a
generic trend sentence (`trendText()`) that can read as unhelpful when evidence is
thin (e.g. "Not enough status evidence to describe a trend."). All subjects also
show this text simultaneously, making the list feel noisy. There's no visual trend —
only a text description — even though a sparkline chart already exists for this
purpose on the lively dashboard (`components/dashboard/student/lively/GradeTrend.tsx`).

## Design

### Minimized (default) card state
- Shows: subject name, status badge — same as today.
- Teaser line: replace the generic `trendText()` sentence with `progress.suggested_action`
  (the personalized recommendation already computed server-side and currently shown
  inside the "Why this status" panel). This is always meaningful per subject/status,
  never a generic "not enough evidence" message, and requires no backend changes.
- Everything else (chart, explanation, evidence tables) stays hidden.

### Expanded (clicked) state
- Clicking the card header toggles the existing `detailsOpen` state (reuse it; no new
  state needed). Keep the chevron affordance on the toggle for discoverability.
- When open, show a new **sparkline trend chart** for that subject above the "Why this
  status" panel, built from `progress.records_used`.
- The rest of the expanded content (explanation, suggested action detail, evidence
  tables, "View full evidence history" nested toggle) is unchanged.

### Shared sparkline component
`GradeSparkline` (and its `sparkPoints`/`stepPath` helpers) currently live inside
`components/dashboard/student/lively/GradeTrend.tsx`, coupled to that page's data
shape (`GradeChronologyRecord`). Extract them into
`components/common/GradeSparkline.tsx`, taking `{ level: GradeLevel; period: string }[]`
(a subset already satisfied by `records_used`), so both the lively dashboard and this
page share one implementation of the ordinal-rank plotting logic instead of duplicating it.

## Out of scope
- No backend/API changes — `suggested_action` and `records_used` already exist on
  `SubjectProgress`.
- No change to the "Manage subjects" section or filters.
- No change to the nested "View full evidence history" table toggle behavior.

## Testing
- Update `frontend/src/test/academic-progress-page.test.tsx` to assert: teaser text
  matches `suggested_action` (not the old trend sentence) while collapsed, and clicking
  a card reveals the sparkline chart region.
