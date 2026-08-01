# UI Redesign Remaining Work Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the approved platform-wide responsive redesign after the shared management foundation and initial System Administrator migrations.

**Architecture:** Extend the tokenized shell and shared dashboard/management primitives already present in `frontend/src/components/common/`. Migrate one role workspace per task, preserving current APIs and adding server pagination only where the existing catalogue response cannot support bounded rendering.

**Tech Stack:** React 18, TypeScript, React Router, React Query v5, Zustand, Vitest, React Testing Library, MSW 2, Vite PWA, Django REST Framework, pytest-django.

## Global Constraints

- Work only on `codex/*` branches; never commit or push directly to `main`.
- Use `var(--color-*)`, `var(--space-*)`, `var(--radius-*)`, and typography tokens; do not add hardcoded hex colors.
- Use `Counsellor` in user-facing copy.
- Preserve minimum 44px touch targets, visible focus, labels, loading states, and toast feedback.
- Write a failing test before each behavior change and run CodeRabbit after each completed task.
- Verify 320, 390, 768, 1024, and 1440 pixel layouts without horizontal page overflow.

---

### Task 1: Adaptive navigation and installed-PWA shell

**Files:**
- Modify: `frontend/src/components/shell/Shell.tsx`
- Modify: `frontend/src/components/shell/Sidebar.tsx`
- Modify: `frontend/src/components/shell/Topbar.tsx`
- Create: `frontend/src/components/shell/MobileBottomNav.tsx`
- Create: `frontend/src/components/shell/MobileMoreSheet.tsx`
- Modify: `frontend/src/styles/shell.css`
- Modify: `frontend/src/test/shell-layout.test.tsx`
- Modify: `frontend/src/test/pwa/PWA.test.tsx`

**Interfaces:**
- Consumes: authenticated user role from `useAuthStore` and existing route definitions from `App.tsx`.
- Produces: role-aware `MobileBottomNav` with four primary destinations and `More`, plus standalone safe-area layout.

- [ ] Add failing shell tests asserting student, counsellor, school-admin, system-admin, and parent destination sets at phone width.
- [ ] Add failing PWA tests for `env(safe-area-inset-bottom)`, standalone navigation persistence, update state, offline state, deep-link refresh, and logout cleanup.
- [ ] Implement `MobileBottomNav` and `MobileMoreSheet` from the exact role mappings in specification section 5.
- [ ] Hide desktop sidebar on authenticated phone layouts while preserving it at 768px and above.
- [ ] Run `npm test -- src/test/shell-layout.test.tsx src/test/pwa/PWA.test.tsx` and `npm run build`.
- [ ] Verify all five roles at 320, 390, 768, and 1440 pixels, then run CodeRabbit on the task diff.

### Task 2: Complete the School Administrator workspace

**Files:**
- Modify: `frontend/src/components/dashboard/admin/SchoolAdminDashboard.tsx`
- Modify: `frontend/src/pages/admin/SchoolStudentsPage.tsx`
- Modify: `frontend/src/pages/admin/SchoolProfilePage.tsx`
- Modify: `frontend/src/pages/admin/SchoolOfferingsPage.tsx`
- Modify: `frontend/src/styles/school-admin.css`
- Modify: `frontend/src/test/school-admin.test.tsx`

**Interfaces:**
- Consumes: shared `ManagementPage`, `ManagementTable`, `ManagementToolbar`, `DetailDrawer`, and `ConfirmDialog` primitives.
- Produces: compact operational dashboard and consistent learner/profile/offering management routes.

- [ ] Add failing tests for compact dashboard metrics, a bounded learner table, one primary row action, overflow actions, bulk assignment, and named confirmations.
- [ ] Replace stacked full-width dashboard metrics with a four-card grid followed by learner and counsellor operational tables.
- [ ] Migrate approved learners to columns `Learner`, `Journey stage`, `Counsellor`, `Last activity`, and `Status`; keep pending requests in a labelled tab on the same route.
- [ ] Align profile and offering forms with labelled tokenized controls, loading states, and toasts.
- [ ] Run `npm test -- src/test/school-admin.test.tsx src/test/management-primitives.test.tsx` and `npm run build`.
- [ ] Verify create, approve, assign, report, remove, and offering-save flows at the acceptance widths, then run CodeRabbit.

### Task 3: Add scalable System Catalogue management

**Files:**
- Modify: `backend/system_admin/views.py`
- Modify: `backend/system_admin/urls.py`
- Modify: `backend/tests/test_system_admin_views.py`
- Modify: `frontend/src/api/systemAdmin.ts`
- Modify: `frontend/src/pages/system-admin/SystemAdminCataloguePage.tsx`
- Modify: `frontend/src/test/msw/handlers.ts`
- Modify: `frontend/src/test/system-admin/SystemAdmin.test.tsx`

**Interfaces:**
- Consumes: catalogue models and current `systemAdminApi` response envelope.
- Produces: paginated catalogue response with `page`, `page_size`, `total`, `results`, and impact counts.

- [ ] Add failing backend tests for search, pathway, track, status, page, page-size bounds, and stable ordering.
- [ ] Implement server filtering and pagination while preserving `{ data, error, message }` envelopes.
- [ ] Add failing frontend tests for bounded rows, filters, result count, detail drawer, and confirmation before status mutation.
- [ ] Migrate the page to shared management primitives and use API pagination instead of rendering the full catalogue.
- [ ] Run `pytest backend/tests/test_system_admin_views.py -v`, the focused frontend suite, and `npm run build`.
- [ ] Verify large-result behavior and browser responsiveness, then run CodeRabbit.

### Task 4: Migrate the Counsellor workspace

**Files:**
- Modify: `frontend/src/components/dashboard/counselor/CounselorDashboard.tsx`
- Modify: `frontend/src/pages/counselor/StudentListPage.tsx`
- Modify: `frontend/src/pages/counselor/StudentDetailPage.tsx`
- Modify: `frontend/src/pages/counselor/NotesListPage.tsx`
- Modify: `frontend/src/styles/counselor.css`
- Modify: `frontend/src/test/counselor.test.tsx`

**Interfaces:**
- Consumes: counsellor API hooks, dashboard primitives, management primitives, and existing intervention mutations.
- Produces: compact caseload dashboard, responsive learner records, and tabbed learner detail.

- [ ] Add failing tests for priority metrics, learner result count, filters, primary review action, overflow actions, and detail tabs.
- [ ] Replace learner cards with responsive table/card records and keep attention reasons as compact badges.
- [ ] Organize learner detail into `Overview`, `Grades`, `Assessment`, `Plan`, `Interventions`, and `Notes` tabs without exposing raw payloads.
- [ ] Keep intervention and note forms bounded, labelled, disabled while saving, and toast-backed.
- [ ] Run `npm test -- src/test/counselor.test.tsx` and `npm run build`.
- [ ] Verify keyboard, focus return, overflow, and confidential-note separation, then run CodeRabbit.

### Task 5: Migrate the Student workspace

**Files:**
- Modify: `frontend/src/components/dashboard/student/StudentDashboard.tsx`
- Modify: `frontend/src/pages/GradesPage.tsx`
- Modify: `frontend/src/pages/CombinationExplorerPage.tsx`
- Modify: `frontend/src/pages/CombinationComparePage.tsx`
- Modify: `frontend/src/pages/LearnerPlanPage.tsx`
- Modify: `frontend/src/pages/AssessmentPage.tsx`
- Modify: `frontend/src/pages/AssessmentResultsPage.tsx`
- Modify: `frontend/src/pages/ParentAccessPage.tsx`
- Modify: `frontend/src/pages/StudentProfilePage.tsx`
- Modify: `frontend/src/test/dashboard.test.tsx`
- Modify: `frontend/src/test/students.test.tsx`

**Interfaces:**
- Consumes: existing student, assessment, guidance, and parent-access APIs.
- Produces: one consistent learner journey with bounded evidence, choices, plan, access, and profile surfaces.

- [ ] Add failing tests for one h1, clear next action, labelled state, bounded content, and phone navigation on every student route.
- [ ] Replace decorative oversized sections with compact evidence summaries and progressive detail disclosure.
- [ ] Preserve save/remove/compare/plan semantics and add named confirmations where actions are destructive.
- [ ] Align all forms and selected states with shared focus, status, button, loading, and toast patterns.
- [ ] Run all student, assessment, guidance, plan, access, and PWA tests plus `npm run build`.
- [ ] Verify the complete starting-to-reviewed learner journey at all acceptance widths, then run CodeRabbit.

### Task 6: Align Parent, public, and authentication surfaces

**Files:**
- Modify: `frontend/src/components/dashboard/parent/ParentDashboard.tsx`
- Modify: `frontend/src/pages/parent/ChildDetailPage.tsx`
- Modify: `frontend/src/components/marketing/PublicNav.tsx`
- Modify: `frontend/src/components/marketing/PublicFooter.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/pages/RegisterPage.tsx`
- Modify: `frontend/src/styles/parent.css`
- Modify: `frontend/src/styles/marketing.css`
- Modify: `frontend/src/styles/auth.css`
- Modify: `frontend/src/test/parent-dashboard.test.tsx`
- Modify: `frontend/src/test/auth.test.tsx`
- Modify: `frontend/src/test/public-nav.test.tsx`

**Interfaces:**
- Consumes: shared brand tokens and existing parent/auth APIs.
- Produces: responsive parent overview/detail and consistent public/authentication language.

- [ ] Add failing tests for parent child switching, disclosure boundaries, public mobile navigation, auth labels, errors, and mobile gutters.
- [ ] Align parent data hierarchy with the student/counsellor evidence terminology while preserving access restrictions.
- [ ] Normalize public and auth colors, radii, controls, focus, and button hierarchy to the dashboard token system.
- [ ] Run the parent, public, auth, and shell tests plus `npm run build`.
- [ ] Verify unauthenticated routes never render authenticated navigation and parent routes expose only approved learner data.
- [ ] Run CodeRabbit on the completed task diff.

### Task 7: Complete accessibility, PWA, and visual-regression closure

**Files:**
- Modify: `frontend/src/test/chart-accessibility.test.tsx`
- Modify: `frontend/src/test/error-recovery.test.tsx`
- Modify: `frontend/src/test/pwa/PWA.test.tsx`
- Create: `frontend/src/test/ui-responsive-contracts.test.tsx`
- Modify: `docs/ui-redesign-progress-and-remaining.md`

**Interfaces:**
- Consumes: all completed role routes and the acceptance matrix in specification section 9.
- Produces: automated and manual evidence that the redesign meets the approved completion criteria.

- [ ] Add automated contracts for one h1, labelled controls, 44px touch targets, focus-visible behavior, reduced motion, and mobile containment.
- [ ] Run the complete frontend suite, complete backend suite, TypeScript/Vite/PWA build, and CodeRabbit ultra review.
- [ ] Test keyboard-only navigation, Escape/focus return, 200% zoom, slow network, offline refresh, install, update, deep link, and logout.
- [ ] Capture approved local-only screenshots at 320, 390, 768, 1024, and 1440 pixels without committing image artefacts.
- [ ] Update `docs/ui-redesign-progress-and-remaining.md` so every remaining slice is marked complete with its verification evidence.
- [ ] Open a draft pull request for human review; do not merge until the visual and functional checklist is approved.

## Self-review result

- Specification coverage: remaining delivery slices 2 through 8 are mapped to Tasks 1 through 7.
- Placeholder scan: every task names its files, behavior, verification command, and review gate.
- Type consistency: shared management primitives and existing API modules are referenced by their current file and component names.
