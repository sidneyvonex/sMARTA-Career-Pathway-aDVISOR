# UI Redesign Slice 2: System Administration Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the system-administrator Schools, Users, and Audit Log pages onto the approved responsive management foundation while preserving all existing API behavior.

**Architecture:** Reuse `ManagementPage`, `ManagementToolbar`, `ManagementTable`, `Pagination`, `DetailDrawer`, `ConfirmDialog`, and `RowActionMenu`. Each route continues to own its React Query state and mutations; the shared components own only presentation, semantics, keyboard interaction, and responsive reflow. Catalogue work is excluded because its server-side filtering contract belongs to a later API slice.

**Tech Stack:** React 18, TypeScript 5.5, React Query 5, vanilla CSS variables, Vitest 2, React Testing Library, MSW 2.

## Global Constraints

- Work only on `codex/ui-ux-pwa-redesign`; do not stage, commit, push, or merge without user approval.
- Preserve all unrelated working-tree changes.
- Keep the current `systemAdminApi` request and response contracts unchanged.
- Use semantic CSS variables and existing management primitives; do not introduce a component library or hardcoded component colors.
- Expose one visible primary row action and one named overflow menu for secondary actions.
- Require a record-named confirmation before activation or deactivation mutations.
- Move verbose audit metadata into a detail drawer; do not print truncated raw JSON in the table.
- Keep search/filter state page-owned and reset pagination to page one after filter changes.
- Standard tables must become labeled records below `768px` without page-level horizontal overflow.
- Follow red-green-refactor for every behavior change.

---

## File map

**Modify:**

- `frontend/src/pages/system-admin/SystemAdminSchoolsPage.tsx` — standard Schools management composition, details, edit/create form, and confirmed status actions.
- `frontend/src/pages/system-admin/SystemAdminUsersPage.tsx` — coordinated user decision fields, details, report action, and confirmed status actions.
- `frontend/src/pages/system-admin/SystemAdminAuditLogPage.tsx` — coordinated audit rows and structured detail drawer.
- `frontend/src/test/system-admin/SystemAdmin.test.tsx` — route integration, action hierarchy, confirmation, and drawer tests.
- `frontend/src/styles/system-admin.css` — route-specific form/detail styles only; shared table styles remain in `management.css`.

### Task 1: Migrate Schools to the management foundation

**Interfaces:**

- Consumes `systemAdminApi.getSchools`, `createSchool`, `updateSchool`, `activateSchool`, and `deactivateSchool` unchanged.
- Produces table columns `School`, `County and code`, `Learners`, `Counsellors`, `Evidence`, and `Status`.
- Produces primary action `View {school name}` and overflow actions `Edit` plus `Activate` or `Deactivate`.

- [ ] **Step 1: Write failing Schools integration expectations**

Require one `h1`, a live result count, a semantic table named `Pilot schools`, named View actions, named overflow triggers, a details drawer, and a record-named confirmation dialog before status mutation.

```tsx
expect(await screen.findByRole('heading', { name: 'Schools', level: 1 })).toBeInTheDocument()
expect(screen.getByRole('table', { name: 'Pilot schools' })).toBeInTheDocument()
expect(screen.getByRole('button', { name: 'View Starehe Boys Centre' })).toBeInTheDocument()
expect(screen.getByRole('button', { name: 'More actions for Starehe Boys Centre' })).toBeInTheDocument()
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run `cd frontend && npm test -- src/test/system-admin/SystemAdmin.test.tsx`.
Expected: the new management-table/action assertions fail against the legacy table.

- [ ] **Step 3: Implement the minimal Schools migration**

Compose the route with shared primitives. Keep the existing create and edit fields and mutations. Render identity and school code together, retain county and operational counts, move phone/email into the detail drawer, and confirm activation changes before mutating.

- [ ] **Step 4: Verify GREEN**

Run the focused system-admin test file and confirm all Schools tests pass.

### Task 2: Migrate Users to the management foundation

**Interfaces:**

- Consumes `systemAdminApi.getUsers`, `activateUser`, and `deactivateUser` unchanged.
- Produces columns `User`, `Role`, `School or county`, `Verification`, `Joined`, and `Status`.
- Produces primary action `View {user name}` and overflow actions for PDF download and confirmed activation changes.

- [ ] **Step 1: Write failing Users integration expectations**

Require a table named `Platform users`, named row actions, a detail drawer containing the full email and affiliation, and a record-named confirmation dialog.

```tsx
expect(await screen.findByRole('table', { name: 'Platform users' })).toBeInTheDocument()
expect(screen.getByRole('button', { name: 'View Jane Doe' })).toBeInTheDocument()
expect(screen.getByRole('button', { name: 'More actions for Jane Doe' })).toBeInTheDocument()
```

- [ ] **Step 2: Run and verify RED**

Run the focused system-admin file. Expected: the row-action and drawer assertions fail against the legacy page.

- [ ] **Step 3: Implement the minimal Users migration**

Reuse existing filters and report hook. Keep the full email in the identity cell secondary line, combine school/county into one decision field, and move PDF plus activation controls into the overflow menu. Disable duplicate mutations while pending.

- [ ] **Step 4: Verify GREEN**

Run the focused file and confirm all Users tests pass.

### Task 3: Migrate Audit Log to structured records

**Interfaces:**

- Consumes `systemAdminApi.getAuditLogs` unchanged.
- Produces columns `Time`, `Actor`, `Event`, `Affected record`, and `Summary`.
- Produces primary action `View details for {event label}`; no destructive secondary action is required.

- [ ] **Step 1: Write failing Audit Log expectations**

Require a table named `Audit log entries`, named View details actions, no raw JSON in visible table cells, and a details drawer with structured key/value content.

```tsx
expect(await screen.findByRole('table', { name: 'Audit log entries' })).toBeInTheDocument()
expect(screen.getByRole('button', { name: /View details for School created/ })).toBeInTheDocument()
expect(screen.queryByText(/\{"/)).not.toBeInTheDocument()
```

- [ ] **Step 2: Run and verify RED**

Run the focused system-admin file. Expected: table naming, details action, or raw-JSON visibility assertions fail.

- [ ] **Step 3: Implement the minimal Audit Log migration**

Generate a short human-readable summary from the existing details object and render all metadata as a definition list in `DetailDrawer`. Keep action/date filters and API pagination unchanged.

- [ ] **Step 4: Verify GREEN**

Run the focused file and confirm all Audit Log tests pass.

### Task 4: Responsive and regression verification

- [ ] Run `npm test -- src/test/system-admin/SystemAdmin.test.tsx src/test/management-primitives.test.tsx src/test/shell-layout.test.tsx`.
- [ ] Run `npm run build` and confirm TypeScript, Vite, manifest, and service-worker generation succeed.
- [ ] Inspect Schools, Users, and Audit Log at `320`, `390`, `768`, and `1440` CSS pixels; confirm exactly one `h1`, no page-level horizontal overflow, readable identity/status/action fields, and closed overlays absent from the accessibility tree.
- [ ] Run CodeRabbit on the uncommitted diff if the CLI is authenticated; otherwise report the authentication blocker without committing.
- [ ] Present the exact diff scope and verification evidence to the user before any Git staging or commit.
