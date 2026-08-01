# UI Redesign Slice 1: Shared Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove the shared page, table, action, pagination, dialog, drawer, loading, empty, and error foundations required by the approved platform redesign.

**Architecture:** Extend the existing dashboard primitives instead of adding a component framework. Small focused components provide management-page composition, accessible row actions, confirmation/detail overlays, responsive records, and pagination. The school-administrator counsellor page is the pilot consumer so the foundation is exercised by production behavior before later role migrations.

**Tech Stack:** React 18, TypeScript 5.5, React Router 6, React Query 5, Zustand 4, vanilla CSS design tokens, Vitest 2, React Testing Library, MSW 2.

## Global Constraints

- Work only on `codex/ui-ux-pwa-redesign`; never implement on `main`.
- Preserve all unrelated working-tree changes.
- Do not add a UI library or change the frontend framework.
- Use existing semantic CSS variables; do not hardcode component colors, spacing, radius, typography, shadows, transitions, or z-index values.
- Every operational row exposes one visible primary action and one overflow menu for secondary actions.
- Destructive actions appear last and require a confirmation dialog naming the affected record.
- Standard tables become labeled records below `768px`; comparison matrices may use contained horizontal scrolling.
- All interactive controls have a minimum `44px` target and visible focus.
- Every mutation shows the existing success or friendly error toast and disables duplicate submission.
- Follow red-green-refactor: add a focused failing test before each production behavior.
- Do not stage, commit, push, open a pull request, or merge until the user reviews the exact diff, test results, screenshots, and CodeRabbit findings. Commit commands below are approval-gated handoff instructions, not authorization to run them automatically.
- Design source: `docs/superpowers/specs/2026-08-01-platform-ui-consistency-pwa-redesign.md`.

---

## File map

**Create:**

- `frontend/src/components/common/management/types.ts` — shared generic action and pagination contracts.
- `frontend/src/components/common/management/RowActionMenu.tsx` — accessible per-record overflow actions.
- `frontend/src/components/common/management/ConfirmDialog.tsx` — destructive-action confirmation and focus restoration.
- `frontend/src/components/common/management/DetailDrawer.tsx` — progressive disclosure for verbose record details.
- `frontend/src/components/common/management/ManagementTable.tsx` — semantic desktop table and labeled mobile records.
- `frontend/src/components/common/management/ManagementToolbar.tsx` — search, filters, result count, and page action layout.
- `frontend/src/components/common/management/Pagination.tsx` — bounded page navigation and page-size selection.
- `frontend/src/components/common/management/ManagementPage.tsx` — shared title, purpose, toolbar, body, and state composition.
- `frontend/src/styles/management.css` — token-driven layout and responsive styling for the new primitives.
- `frontend/src/test/management-primitives.test.tsx` — behavior, semantics, keyboard, and responsive-label contract tests.

**Modify:**

- `frontend/src/pages/admin/CounselorManagementPage.tsx` — production pilot for the shared foundations.
- `frontend/src/test/school-admin.test.tsx` — pilot integration and mutation tests.
- `frontend/src/styles/school-admin.css` — remove styles made obsolete by the pilot migration only.

---

### Task 1: Define shared management contracts and row action menu

**Files:**

- Create: `frontend/src/components/common/management/types.ts`
- Create: `frontend/src/components/common/management/RowActionMenu.tsx`
- Create: `frontend/src/test/management-primitives.test.tsx`

**Interfaces:**

- Produces `ManagementAction`, `ManagementColumn<T>`, and `PaginationState`.
- Produces `RowActionMenu({ recordLabel, actions, disabled? })`.
- Later table and page tasks consume these exact exports.

- [ ] **Step 1: Write failing action-menu tests**

Add tests that require an accessible trigger, keyboard opening, action execution, Escape close, outside-click close, and destructive actions rendered last:

```tsx
const actions: ManagementAction[] = [
  { id: 'edit', label: 'Edit', onSelect: vi.fn() },
  { id: 'remove', label: 'Remove', tone: 'danger', onSelect: vi.fn() },
]

render(<RowActionMenu recordLabel="Grace Wanjiku" actions={actions} />)

const trigger = screen.getByRole('button', {
  name: 'More actions for Grace Wanjiku',
})
await userEvent.click(trigger)
expect(screen.getByRole('menu')).toBeInTheDocument()
expect(screen.getAllByRole('menuitem').map(item => item.textContent)).toEqual([
  'Edit',
  'Remove',
])
await userEvent.keyboard('{Escape}')
expect(screen.queryByRole('menu')).not.toBeInTheDocument()
expect(trigger).toHaveFocus()
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
cd frontend && npm test -- src/test/management-primitives.test.tsx
```

Expected: FAIL because the management contracts and `RowActionMenu` do not exist.

- [ ] **Step 3: Implement the contracts and minimal menu**

Use these contracts:

```ts
export interface ManagementAction {
  id: string
  label: string
  onSelect: () => void
  tone?: 'default' | 'danger'
  disabled?: boolean
}

export interface ManagementColumn<T> {
  key: string
  label: string
  render: (record: T) => ReactNode
  priority?: 'identity' | 'essential' | 'secondary' | 'action'
  align?: 'start' | 'center' | 'end'
}

export interface PaginationState {
  page: number
  pageSize: 10 | 25 | 50
  total: number
}
```

`RowActionMenu` owns only its open state. It sorts `tone: 'danger'` actions after non-destructive actions, closes after selection, closes on Escape or outside pointer interaction, and restores focus to its trigger. Do not introduce global menu state.

- [ ] **Step 4: Verify GREEN**

Run the focused file. Expected: all action-menu tests PASS.

- [ ] **Step 5: Hold the commit for approval**

After user approval only:

```bash
git add frontend/src/components/common/management/types.ts frontend/src/components/common/management/RowActionMenu.tsx frontend/src/test/management-primitives.test.tsx
git commit -m "feat(ui): add accessible row action menu"
```

### Task 2: Add confirmation dialog and detail drawer primitives

**Files:**

- Create: `frontend/src/components/common/management/ConfirmDialog.tsx`
- Create: `frontend/src/components/common/management/DetailDrawer.tsx`
- Modify: `frontend/src/test/management-primitives.test.tsx`

**Interfaces:**

- Produces `ConfirmDialog({ open, title, description, confirmLabel, pending, onConfirm, onClose })`.
- Produces `DetailDrawer({ open, title, children, onClose })`.
- Both restore focus to the previously focused control and lock body scrolling only while open.

- [ ] **Step 1: Write failing overlay tests**

Require `role="dialog"`, `aria-modal="true"`, named headings, initial focus, Tab containment, Escape close, disabled pending confirmation, body-scroll restoration, and trigger-focus restoration.

```tsx
render(
  <ConfirmDialog
    open
    title="Remove Grace Wanjiku?"
    description="Grace will no longer be available for learner assignments."
    confirmLabel="Remove counsellor"
    pending={false}
    onConfirm={onConfirm}
    onClose={onClose}
  />,
)

expect(screen.getByRole('dialog', { name: 'Remove Grace Wanjiku?' }))
  .toHaveAttribute('aria-modal', 'true')
await userEvent.click(screen.getByRole('button', { name: 'Remove counsellor' }))
expect(onConfirm).toHaveBeenCalledOnce()
```

- [ ] **Step 2: Run the focused tests and verify RED**

Expected: FAIL because neither overlay exists.

- [ ] **Step 3: Implement focused overlay behavior**

Render overlays with `createPortal(..., document.body)`. Use a shared internal focusable-elements query inside each component; do not add a dependency. Close on the backdrop only when `event.target === event.currentTarget`. Do not close a pending confirmation dialog.

- [ ] **Step 4: Verify GREEN and cleanup behavior**

Run the focused tests twice to expose leaked listeners. Expected: PASS both times and `document.body.style.overflow` restored.

- [ ] **Step 5: Hold the commit for approval**

After user approval only:

```bash
git add frontend/src/components/common/management/ConfirmDialog.tsx frontend/src/components/common/management/DetailDrawer.tsx frontend/src/test/management-primitives.test.tsx
git commit -m "feat(ui): add accessible management overlays"
```

### Task 3: Build the responsive management table

**Files:**

- Create: `frontend/src/components/common/management/ManagementTable.tsx`
- Modify: `frontend/src/test/management-primitives.test.tsx`
- Create: `frontend/src/styles/management.css`

**Interfaces:**

- Consumes `ManagementColumn<T>` and `ManagementAction`.
- Produces `ManagementTable<T>` with `ariaLabel`, `records`, `columns`, `getKey`, `getRecordLabel`, `getPrimaryAction`, `getSecondaryActions`, and `empty`.
- Keeps `ResponsiveDataList` unchanged until migrations prove it can be retired safely.

- [ ] **Step 1: Write failing semantic and record-label tests**

Use two counsellor fixtures. Assert table name, column headers, `data-label` values, a visible primary action for every row, and an overflow trigger labeled with the record name.

```tsx
expect(screen.getByRole('table', { name: 'School counsellors' })).toBeInTheDocument()
expect(screen.getByRole('button', { name: 'View Grace Wanjiku' })).toBeInTheDocument()
expect(screen.getByRole('button', {
  name: 'More actions for Grace Wanjiku',
})).toBeInTheDocument()
expect(screen.getByText('grace@school.test').closest('td'))
  .toHaveAttribute('data-label', 'Counsellor')
```

- [ ] **Step 2: Run and verify RED**

Expected: FAIL because `ManagementTable` does not exist.

- [ ] **Step 3: Implement the generic table**

Use a semantic `<table>` at all widths. CSS changes rows and cells to labeled block records below `768px`, while the visually hidden table header remains available to assistive technology. Primary actions and the overflow menu occupy the final action cell. Long values use `overflow-wrap: anywhere` and all grid/flex children use `min-width: 0`.

- [ ] **Step 4: Add CSS contract assertions**

Assert the action cell has `data-priority="action"` and essential cells expose `data-priority="essential"`. Do not test pixel appearance in JSDOM; reserve layout measurements for Playwright.

- [ ] **Step 5: Verify GREEN**

Run `management-primitives.test.tsx`. Expected: all table and menu tests PASS.

- [ ] **Step 6: Hold the commit for approval**

After user approval only:

```bash
git add frontend/src/components/common/management/ManagementTable.tsx frontend/src/styles/management.css frontend/src/test/management-primitives.test.tsx
git commit -m "feat(ui): add responsive management table"
```

### Task 4: Add management toolbar and bounded pagination

**Files:**

- Create: `frontend/src/components/common/management/ManagementToolbar.tsx`
- Create: `frontend/src/components/common/management/Pagination.tsx`
- Modify: `frontend/src/test/management-primitives.test.tsx`

**Interfaces:**

- Produces `ManagementToolbar({ resultCount, search, filters, pageAction, bulkActions? })`.
- Produces `Pagination({ state, onPageChange, onPageSizeChange })`.
- Page-size values are limited to `10`, `25`, and `50`.

- [ ] **Step 1: Write failing toolbar and pagination tests**

Require a visible search label, results summary live region, filter slot, disabled Previous on page one, disabled Next on the final page, and reset to page one when page size changes.

```tsx
expect(screen.getByText('38 counsellors')).toHaveAttribute('aria-live', 'polite')
expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled()
await userEvent.selectOptions(screen.getByLabelText('Rows per page'), '50')
expect(onPageSizeChange).toHaveBeenCalledWith(50)
```

- [ ] **Step 2: Run and verify RED**

Expected: FAIL because toolbar and pagination components do not exist.

- [ ] **Step 3: Implement minimal controlled components**

Pagination calculates `pageCount = Math.max(1, Math.ceil(total / pageSize))` and announces `Page {page} of {pageCount}`. It never accepts page zero or a page above `pageCount`. The toolbar provides layout only; pages own query/filter state.

- [ ] **Step 4: Verify GREEN**

Run the focused tests. Expected: all toolbar and pagination tests PASS.

- [ ] **Step 5: Hold the commit for approval**

After user approval only:

```bash
git add frontend/src/components/common/management/ManagementToolbar.tsx frontend/src/components/common/management/Pagination.tsx frontend/src/test/management-primitives.test.tsx
git commit -m "feat(ui): add management toolbar and pagination"
```

### Task 5: Compose the standard management page and states

**Files:**

- Create: `frontend/src/components/common/management/ManagementPage.tsx`
- Modify: `frontend/src/test/management-primitives.test.tsx`
- Modify: `frontend/src/styles/management.css`

**Interfaces:**

- Produces `ManagementPage({ title, eyebrow?, description, pageAction?, toolbar?, loading, error, onRetry?, children })`.
- Reuses `SectionHeader`, `LoadingSkeleton`, `ErrorState`, and page-provided `EmptyState` rather than duplicating state components.

- [ ] **Step 1: Write failing composition tests**

Assert exactly one `h1`, the page action follows the heading region, loading uses a named status, error retains Retry, and loaded children do not render during initial loading.

- [ ] **Step 2: Run and verify RED**

Expected: FAIL because `ManagementPage` does not exist.

- [ ] **Step 3: Implement composition without owning server state**

`ManagementPage` chooses initial loading, blocking error, or loaded body. It does not call React Query, mutate URLs, or infer data emptiness. This keeps the component reusable and prevents hidden data behavior.

- [ ] **Step 4: Verify GREEN**

Run both `management-primitives.test.tsx` and `dashboard-primitives.test.tsx`. Expected: PASS with no heading regression.

- [ ] **Step 5: Hold the commit for approval**

After user approval only:

```bash
git add frontend/src/components/common/management/ManagementPage.tsx frontend/src/styles/management.css frontend/src/test/management-primitives.test.tsx
git commit -m "feat(ui): add standard management page composition"
```

### Task 6: Migrate the school counsellor page as the production pilot

**Files:**

- Modify: `frontend/src/pages/admin/CounselorManagementPage.tsx`
- Modify: `frontend/src/test/school-admin.test.tsx`
- Modify: `frontend/src/styles/school-admin.css`

**Interfaces:**

- Consumes all shared management primitives from Tasks 1–5.
- Preserves `schoolAdminApi.getCounselors`, `addCounselor`, and `removeCounselor` signatures.
- Produces one visible `View workload` action and overflow action `Remove` for each counsellor.

- [ ] **Step 1: Replace integration expectations before production code**

Update the existing counsellor-page test to require:

```tsx
expect(await screen.findByRole('heading', { name: 'Counsellors', level: 1 }))
  .toBeInTheDocument()
expect(screen.getByText('2 counsellors')).toBeInTheDocument()
expect(screen.getByRole('button', { name: 'View workload for Grace Wanjiku' }))
  .toBeInTheDocument()
expect(screen.getByRole('button', {
  name: 'More actions for Grace Wanjiku',
})).toBeInTheDocument()
```

Open the overflow menu, select Remove, verify the named confirmation dialog, confirm, and assert the established POST removal request and success toast. Add a cancellation test proving no request runs.

- [ ] **Step 2: Run the school-admin test and verify RED**

Run:

```bash
cd frontend && npm test -- src/test/school-admin.test.tsx -t "counsellor"
```

Expected: FAIL because the current page uses inline invite/search layout and two-click button text instead of the approved management components and dialog.

- [ ] **Step 3: Migrate the page without changing the API**

Use `ManagementPage`, `ManagementToolbar`, and `ManagementTable`. Keep client-side search for this pilot because the current counsellor collection is bounded; server pagination belongs to the later catalogue and role-data slices. Put the invite form in the page-action region as a bounded section. The visible `View workload` action opens `DetailDrawer` with the counsellor identity, contact, joined date, and assigned-learner count. Use `ConfirmDialog` for Remove. Do not invent a route or leave a dead control.

- [ ] **Step 4: Remove only obsolete page CSS**

Delete selectors used solely by the replaced counsellor page. Retain `.admin-person` wrapping and any selectors still used by learners, offerings, or dashboards. Confirm usage with `rg` before deletion.

- [ ] **Step 5: Verify GREEN and regressions**

Run:

```bash
cd frontend && npm test -- src/test/management-primitives.test.tsx src/test/dashboard-primitives.test.tsx src/test/school-admin.test.tsx
cd frontend && npm run build
```

Expected: focused suites PASS and production/PWA build succeeds.

- [ ] **Step 6: Hold the commit for approval**

After user approval only:

```bash
git add frontend/src/pages/admin/CounselorManagementPage.tsx frontend/src/test/school-admin.test.tsx frontend/src/styles/school-admin.css
git commit -m "refactor(admin): adopt shared counsellor table"
```

### Task 7: Browser verification, accessibility evidence, and review gate

**Files:**

- No production files unless a verified defect requires a new red-green cycle.
- Local-only evidence: `.playwright-mcp/ui-ux-pwa-audit/`.

**Interfaces:**

- Consumes the complete uncommitted Slice 1 diff.
- Produces test output, viewport evidence, accessibility findings, and CodeRabbit findings for user review.

- [ ] **Step 1: Run the complete focused verification set**

```bash
cd frontend && npm test -- src/test/management-primitives.test.tsx src/test/dashboard-primitives.test.tsx src/test/school-admin.test.tsx src/test/shell-layout.test.tsx
cd frontend && npm run build
```

Expected: all selected tests PASS and production/PWA build succeeds.

- [ ] **Step 2: Verify the pilot page with Playwright**

At `/admin/counselors`, check `320x568`, `360x800`, `390x844`, `768x1024`, `1024x768`, `1440x900`, and `1920x1080`.

For each representative mode confirm:

- exactly one `h1`;
- no document-level horizontal overflow;
- full long-email visibility;
- one compact record-action region;
- overflow menu keyboard operation and focus restoration;
- confirmation dialog focus containment and cancellation;
- no action, toast, menu, or final record is obscured;
- 200% zoom remains usable;
- reduced motion removes nonessential transitions.

Store screenshots only under `.playwright-mcp/`; never commit them.

- [ ] **Step 3: Run CodeRabbit on the uncommitted diff**

Review only Slice 1 files. For every actionable finding, invoke the receiving-code-review workflow, reproduce it, add a failing test, implement the minimal correction, and rerun the focused verification.

- [ ] **Step 4: Present the user checkpoint**

Report:

- exact files changed;
- RED and GREEN test evidence;
- production build result;
- browser viewport evidence;
- accessibility results;
- CodeRabbit findings and dispositions;
- remaining audit findings assigned to later slices.

Do not stage, commit, or push. Wait for explicit user approval.

---

## Later slice plan boundaries

After Slice 1 is implemented and approved, write separate executable plans in this order:

1. adaptive role navigation and installed-PWA shell;
2. backend and frontend catalogue pagination/performance;
3. system- and school-administrator page migrations;
4. counsellor dashboard, learner workspace, interventions, and notes;
5. student dashboard, grades, exploration, comparison, plan, assessment, access, and profile;
6. parent dashboard/detail plus public/auth token alignment;
7. full accessibility, PWA, viewport, interaction, and visual-regression closure.

Each later plan must consume the exact shared contracts proven by this slice, receive its own red-green cycles and CodeRabbit gate, and remain uncommitted until the user approves its diff.
