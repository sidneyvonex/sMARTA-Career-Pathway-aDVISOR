# Smarta Shauri Five-County Pilot Execution Plan

**Date:** 2026-07-30  
**Specification:** `docs/superpowers/specs/2026-07-30-pilot-product-spec.md`  
**Execution style:** Sequential vertical slices, test-first, one logical commit per task  
**Target:** Final-project presentation pilot, not national production release

## Current execution status

**Active sprint:** Sprint 6 - Counsellor intervention workflow

**Completed:** Sprint 0 implementation baseline; Sprint 1 correctness and safety blockers; Sprint 2 shared authenticated design system; Sprint 3 pilot framework and combination domain; Sprint 4 complete learner evidence, interest, comparison and action-plan journey; Sprint 5 learner-approved parent access, support dashboard and child detail

**Next:** Task 6.3 counsellor priority dashboard redesign

**Outstanding baseline check:** Full backend regression suite (Task 3.2 focused and affected-domain suites pass; the full run exceeded the 120-second command window after 57 passing tests during Task 3.1)

| Commit | Delivered change |
|---|---|
| `b384bda` | Five-county product specification and execution baseline |
| `c62d297` | Repository rules limited to the two tracked pilot planning documents |
| `3c09d4e` | Redesigned learner dashboard and student experience baseline |
| `39be6b4` | Public landing-page mobile overflow correction |
| `ab53d07` | Canonical CBE grade ordering, labels, points, chart and PDF fixtures |
| `2e3d9cf` | Current Grade 10 pilot catalogue with safe retirement of obsolete records |
| `3eec101` | Authenticated API cache exclusion and logout data cleanup |
| `f30a99a` | Active-school validation and pending learner membership |
| `b24ba8d` | Advisory interest-alignment language across learner, parent, counsellor, public and PDF surfaces |
| `ba721c6` | Shared, role-aware dashboard primitives with parent and counsellor adoption |
| `3204ce1` | Standardized authenticated shell, route context, mobile navigation and offline status |
| `2897357` | Application and route error boundaries with retryable query recovery |
| `ea4e7ab` | Source-dated guidance framework, pathway tracks, three-subject combinations and school offerings |
| `cce4907` | Curated Ministry-code pilot catalogue and representative five-county demonstration offerings |
| `9b84c28` | Public source-dated guidance APIs with catalogue filters and bounded query counts |
| `d7ab5e1` | Permission-tested school offering reads and atomic full-replacement updates |
| `88f2109` | Typed guidance frontend client, unified query keys and complete MSW contracts |
| `566de40` | Learner evidence and aggregated grade summaries with calculated next actions |
| `457c21e` | Audited school verification and immutable provenance for learner grades |
| `eee1684` | Versioned assessment attempts, explanation snapshots and expiring learner-scoped drafts |
| `a9219f2` | Learner-saved and provisional combinations with pilot limits and summary integration |
| `3d2db97` | Responsive five-county learner combination explorer with save actions |
| `38836be` | Evidence-led two-or-three-choice comparison with curated related routes |
| `737d96b` | Learner action plan, evidence gaps, milestones and review readiness |
| `7b2c62f` | Evidence-to-action learner dashboard with calculated next action |
| `dac4407` | Learner-approved parent access, revocation and pilot identity notice |
| `257b981` | Parent support dashboard with learner plan and next-action context |
| `681d874` | Learner-approved parent child summary with evidence, plan, notes and report access |
| `80d27ec` | Explicit, non-predictive counsellor attention reasons with bounded caseload loading |
| `6de164d` | Pilot interventions with agreed actions, follow-ups and explicit visibility |

## 1. How to use this plan

Execute tasks in order. Do not begin a later sprint until the prior sprint's exit gate passes.

For every implementation task:

1. Read the referenced files.
2. Write or update the failing test first.
3. Implement the smallest complete change.
4. Run focused tests.
5. Run the sprint regression tests.
6. Check desktop and mobile behavior when frontend code changes.
7. Review the diff.
8. Commit one logical change.

Use commit format:

```text
feat|fix|test|refactor|docs(scope): concise description
```

Do not mix the current uncommitted redesign with unrelated backend migrations in one commit. Before implementation starts, intentionally separate and commit or stash the current student/public redesign work.

## 2. Priority model

### P0 - presentation blockers

- Education data is correct.
- Sensitive authenticated data is not cached.
- Current redesign is stable and shared across roles.
- Learner can complete the evidence -> guidance -> comparison -> plan flow.
- Every role has a coherent dashboard.
- Demo data and full presentation flow are repeatable.

### P1 - makes the pilot operational

- School-link approval.
- School offerings.
- Parent access approval/revocation.
- Counsellor attention reasons and follow-up.
- System-admin pilot metrics and audit visibility.
- Updated learner report.

### P2 - include only if P0/P1 are stable

- CSV roster import.
- Full framework catalogue editing UI.
- Advanced cohort charts.
- Rich notification scheduling.
- Multiple report templates.

## 3. Delivery estimate

Estimates are focused engineering days for one developer familiar with the repository. They are planning ranges, not deadlines.

| Sprint | Outcome | Estimate |
|---|---|---:|
| 0 | Stabilize current redesign and establish baseline | 1-2 days |
| 1 | Correctness and safety blockers | 2-4 days |
| 2 | Shared authenticated design system | 3-4 days |
| 3 | Pilot framework and combination domain | 4-6 days |
| 4 | Complete learner decision-and-plan journey | 5-7 days |
| 5 | Parent support and access workflow | 3-4 days |
| 6 | Counsellor intervention workflow | 3-5 days |
| 7 | School onboarding, offerings and cohort workflow | 4-6 days |
| 8 | System admin and public-content alignment | 3-5 days |
| 9 | Reports, accessibility, PWA, demo data and presentation hardening | 4-6 days |
| **Total** | Full pilot | **32-49 focused days** |

If less time is available, use the cut line in Section 17.

## 4. Target route map

Existing routes should remain compatible. Add only routes needed to make the pilot flow understandable.

```text
PUBLIC
/                         Home
/about                    About
/pathways                 Public pathways and tracks
/how-it-works             End-to-end process
/for-schools              School pilot proposition

STUDENT
/                         Student dashboard
/profile                  Profile evidence
/grades                   Academic evidence
/assessment               Interest assessment
/assessment/results       Guidance results
/explore                  Pathway/track/combination explorer
/compare                  Saved-combination comparison
/plan                     Provisional plan and milestones
/access                   Parent/school access

PARENT
/                         Parent dashboard
/parent/child/:id         Child evidence/plan summary

COUNSELLOR
/                         Counsellor dashboard
/counselor/students       Caseload
/counselor/students/:id   Learner workspace
/counselor/notes          Notes/follow-ups

SCHOOL ADMIN
/                         School dashboard
/admin/students           Students and link requests
/admin/counselors         Counsellors and assignments
/admin/school             School profile
/admin/offerings          Offered combinations

SYSTEM ADMIN
/                         Pilot-health dashboard
/system-admin/schools     Schools
/system-admin/users       Users
/system-admin/framework   Pilot framework catalogue
/system-admin/audit-log   Audit activity
```

## 5. File ownership map

### Existing files to extend

- `backend/accounts/models.py`
- `backend/accounts/serializers.py`
- `backend/accounts/views.py`
- `backend/students/models.py`
- `backend/students/serializers.py`
- `backend/students/views.py`
- `backend/riasec/models.py`
- `backend/riasec/scoring.py`
- `backend/riasec/views.py`
- `backend/parents/models.py`
- `backend/parents/serializers.py`
- `backend/parents/views.py`
- `backend/counselors/models.py`
- `backend/counselors/views.py`
- `backend/school_admin/views.py`
- `backend/system_admin/models.py`
- `backend/system_admin/views.py`
- `backend/reports/views.py`
- `backend/reports/pdf_builder.py`
- `frontend/src/App.tsx`
- `frontend/src/components/shell/*`
- `frontend/src/components/dashboard/*`
- `frontend/src/api/*`
- `frontend/src/styles/theme.css`
- `frontend/src/styles/shell.css`
- `frontend/vite.config.ts`

### New backend domain

Create a focused `backend/guidance/` Django app:

```text
guidance/
  admin.py
  apps.py
  migrations/
  models.py
  serializers.py
  urls.py
  views.py
  services.py
  seed_data.py
```

This app owns tracks, combinations, school offerings, learner choices and plans. Continue using the existing `riasec.Pathway` records for the three top-level pathways during the pilot.

### New frontend areas

```text
frontend/src/api/guidance.ts
frontend/src/components/common/dashboard/*
frontend/src/components/guidance/*
frontend/src/pages/ExplorePage.tsx
frontend/src/pages/ComparePage.tsx
frontend/src/pages/PlanPage.tsx
frontend/src/pages/AccessPage.tsx
frontend/src/pages/admin/SchoolOfferingsPage.tsx
frontend/src/pages/system-admin/SystemAdminFrameworkPage.tsx
frontend/src/styles/guidance.css
frontend/src/styles/role-dashboard.css
```

## 6. Sprint 0 - Stabilize the current redesign

### Outcome

The current public-page redesign and lively student-dashboard work are understandable, testable and separated from future work.

### Task 0.1 - Preserve and classify current work

- [x] Review `git diff --stat` and `git diff`.
- [x] Separate public/student redesign files from unrelated changes.
- [x] Confirm no generated PDF or local design artifacts will be included in a product-code commit.
- [ ] Record the current visual baseline at desktop, tablet and 360px mobile. Desktop and 360px are verified; tablet remains.

Acceptance:

- The current redesign has an intentional change list.
- No user work is discarded.
- The next implementation branch starts from a known state.

### Task 0.2 - Fix existing frontend regressions

Tests:

- `frontend/src/test/dashboard.test.tsx`
- `frontend/src/test/parent-dashboard.test.tsx`
- `frontend/src/test/school-admin.test.tsx`

Work:

- [x] Diagnose the parent dashboard timeout. It did not reproduce against the current redesign baseline.
- [x] Diagnose the school-admin loading/assertion failure. It did not reproduce against the current redesign baseline.
- [x] Remove material `act()` warnings in affected tests.
- [x] Keep MSW data aligned with the current dashboard contracts.

Acceptance:

- `npm test` passes.
- No test depends on arbitrary delays.

### Task 0.3 - Establish quality baseline

- [ ] Run the full backend test suite. Focused grade/student/report suites pass: 77 tests.
- [x] Run frontend tests: 25 files and 141 tests passed.
- [x] Run frontend production build.
- [x] Record baseline bundle sizes and known warnings. Main JS gzip: 135.92 kB; CSS gzip: 20.94 kB before Task 1.1.
- [x] Confirm the five pilot counties remain unchanged.

Exit gate:

```powershell
cd backend
.\venv\Scripts\pytest tests/ -q

cd ..\frontend
npm test
npm run build
```

All commands pass before Sprint 1.

## 7. Sprint 1 - Correctness and safety blockers

### Outcome

The product no longer displays known incorrect grade semantics, inactive school links or unsafe private API caches.

### Task 1.1 - Correct performance levels

Files:

- `backend/students/models.py`
- new student migration
- `backend/reports/views.py`
- `backend/reports/pdf_builder.py`
- `frontend/src/api/students.ts`
- `frontend/src/components/students/GradeEntryForm.tsx`
- `frontend/src/components/students/GradeHistory.tsx`
- `frontend/src/components/dashboard/student/StudentDashboard.tsx`
- related tests and MSW fixtures

Work:

- [x] Correct labels so Level 1 is higher than Level 2 in each band.
- [x] Define one canonical ordering utility in backend and frontend.
- [x] Remove arbitrary dashboard percentage conversion.
- [x] Display trends as ordered performance bands or clearly labelled points.
- [x] Update report labels and test fixtures.

Verification:

- Backend student/model/report suites: 77 passed.
- Frontend student/dashboard suites: 16 passed.
- Student migration drift check: no changes detected.
- Production build: passed; main JS gzip 135.96 kB, CSS gzip 21.03 kB.
- Commit: `ab53d07`.

Acceptance:

- Every UI, API and report orders `EE1 > EE2 > ME1 > ME2 > AE1 > AE2 > BE1 > BE2`.
- No learner grade chart implies a raw percentage.

### Task 1.2 - Correct the Grade 10 catalogue

Files:

- new migration superseding `backend/students/migrations/0003_seed_subjects.py`
- `backend/students/models.py`
- `backend/tests/test_students_*`
- frontend subject fixtures/tests

Work:

- [x] Keep Grade 9 learning areas required by the pilot.
- [x] Replace duplicate junior-style Grade 10 seed data with current Senior School core/elective names needed by the curated pilot combinations.
- [x] Preserve existing student records safely through a forward data migration.
- [x] Mark obsolete seeded subjects inactive rather than deleting referenced rows.

Verification:

- Source check: KICD Grade 10 curriculum designs and Ministry Senior School combinations, checked 2026-07-30.
- Backend student/model/view suites: 53 passed.
- Frontend student/dashboard suites: 17 passed.
- Student migration drift check: no changes detected.
- Production build: passed; main JS gzip 135.99 kB, CSS gzip 21.03 kB.
- Commit: `2e3d9cf`.

Acceptance:

- Grade 10 selection does not show Integrated Science/Social Studies as a duplicated junior catalogue.
- Every seeded combination in Sprint 3 can resolve its subjects.

### Task 1.3 - Stop caching authenticated API data

Files:

- `frontend/vite.config.ts`
- `frontend/src/hooks/usePWAUpdate.tsx`
- `frontend/src/test/pwa/PWA.test.tsx`

Work:

- [x] Remove the broad `/api/v1/` `StaleWhileRevalidate` rule.
- [x] Cache only explicitly public framework endpoints later. No API response is runtime-cached in the current build.
- [x] Version the cache name.
- [x] Remove legacy private API caches during service-worker activation.
- [x] Clear user-scoped local drafts and in-memory queries on logout.

Verification:

- PWA cache and logout suites: 23 passed.
- Full frontend suite: 25 files and 150 tests passed.
- Production PWA build: passed; generated service worker has no API caching route.
- Generated service worker imports legacy `api-cache` cleanup and excludes `/api/` image URLs.
- Commit: `3eec101`.

Acceptance:

- Authenticated student, parent, counsellor and admin responses are never served from Workbox cache.
- A test proves the private route pattern is excluded.

### Task 1.4 - Validate active school joins

Files:

- `backend/accounts/serializers.py`
- `backend/accounts/views.py`
- `backend/tests/test_accounts_views.py`

Work:

- [x] Reject inactive school codes.
- [x] Store school-linked registration as pending approval rather than silently trusted.
- [x] Preserve self-guided registration.

Verification:

- Active-code, pending-state, profile and access-control backend tests pass.
- Broad affected backend run: 143 tests passed; its one stale active-membership fixture was corrected and the 3 focused permission checks then passed.
- Frontend profile/auth/dashboard suites: 23 passed.
- Production build: passed; main JS gzip 136.12 kB, CSS gzip 21.03 kB.
- Pending learners cannot be assigned to counsellors or accessed through school-admin report authorization.
- Commit: `f30a99a`.

Acceptance:

- Invalid/inactive code gives a friendly 400 response.
- Pending membership is visible to the learner.

### Task 1.5 - Correct high-risk language

Files:

- `frontend/src/components/assessment/RecommendationCards.tsx`
- `frontend/src/pages/AssessmentResultsPage.tsx`
- parent/counsellor dashboard components
- `backend/reports/pdf_builder.py`

Work:

- [x] Replace "fit percentage" presentation with "interest alignment."
- [x] Add a clear advisory explanation.
- [x] Remove placement/success implications.
- [x] Keep the numeric value internal only if needed for ranking during the pilot.

Verification:

- Backend report/PDF suite: 29 passed.
- Focused learner, parent, counsellor, dashboard and public-page frontend suites: 56 passed.
- Full frontend regression suite: passed, including 10 PWA tests.
- Production build: passed; main JS gzip 136.29 kB, CSS gzip 21.08 kB.
- Removed the percentage-based pathway donut and replaced it with an explicitly ranked exploration list.
- Static terminology audit found no remaining user-facing fit/match percentage claims in application or report surfaces.
- Commit: `b24ba8d`.

Exit gate:

- [x] Focused backend/frontend tests pass.
- [x] Production build passes.
- [x] Shared-device PWA protections remain covered by the 10-test PWA suite and the generated service worker build.
- [x] Correct terminology appears in learner, parent, counsellor and PDF surfaces.

## 8. Sprint 2 - Shared authenticated design system

### Outcome

All role dashboards can adopt the student/public visual direction without copying large blocks of code.

### Task 2.1 - Extract reusable dashboard primitives

Create:

- `frontend/src/components/common/dashboard/DashboardHero.tsx`
- `MetricCard.tsx`
- `SectionHeader.tsx`
- `ActionCard.tsx`
- `StatusBadge.tsx`
- `EmptyState.tsx`
- `ErrorState.tsx`
- `LoadingSkeleton.tsx`
- `ResponsiveDataList.tsx`
- `ActivityList.tsx`

Work:

- [x] Extract stable concepts from `lively/*`.
- [x] Accept role-specific color/accent variants through props/classes.
- [x] Keep visual values connected to the shared theme tokens.
- [x] Remove hardcoded inline layout/color styles from migrated areas.
- [x] Add component tests for interactive behavior and accessibility labels.

Acceptance:

- [x] Student dashboard retains its specialized hero and card composition while reusing the shared section-header contract.
- [x] Parent and counsellor dashboards render with the same hero, state, section and action/metric primitives.

Verification:

- Shared primitive contract suite: 6 tests passed.
- Focused dashboard, parent and counsellor integration suites: 30 tests passed.
- Full frontend regression suite: 26 files and 160 tests passed.
- Production PWA build: passed; main JS gzip 137.17 kB, CSS gzip 23.32 kB.
- Static review: migrated parent/counsellor areas have no inline layout or color styles; student inline styles only set existing animation-order custom properties.
- Authenticated live-browser review was unavailable because the local Django/MySQL connection rejected TLS credentials. The public shell loaded successfully; no database configuration was changed.
- Commit: `ba721c6`.

### Task 2.2 - Standardize authenticated page layout

Files:

- `frontend/src/components/shell/Shell.tsx`
- `Sidebar.tsx`
- `Topbar.tsx`
- `frontend/src/styles/shell.css`
- new `frontend/src/styles/role-dashboard.css`

Work:

- [x] Define common content width, page spacing and responsive breakpoints.
- [x] Add consistent page title/breadcrumb/action positions.
- [x] Add mobile navigation behavior for all roles.
- [x] Add global offline indicator placeholder.
- [x] Ensure notification and account actions remain reachable at 360px.

Verification:

- Shell contract suite: 4 tests passed, covering route context, mobile open/close/Escape behavior, the shared content container and offline state.
- Focused shell, notification and dashboard regression suites: 22 tests passed.
- Full frontend regression suite: 27 files and 164 tests passed.
- Production PWA build: passed; main JS gzip 137.77 kB, CSS gzip 23.99 kB.
- Static responsive review: 44px notification/account/navigation targets remain visible at 360px; content spacing changes at 900px and 400px; the shared role-page header stacks at 680px.
- Reduced-motion mode removes shell, drawer-overlay and skip-link transitions.
- Authenticated live-browser review remains unavailable because the local Django/MySQL connection rejects TLS credentials; no database configuration was changed.
- Commit: `3204ce1`.

### Task 2.3 - Route error and recovery boundary

- [x] Add application/route error boundary.
- [x] Add reusable retry state.
- [x] Ensure query errors do not leave blank screens.
- [x] Log unexpected frontend errors in development.

Verification:

- Boundary and reusable recovery contract suite: 2 tests passed.
- Focused recovery, school-management and dashboard suites: 23 tests passed.
- Query-failure coverage now includes grade data, school profile, counsellor list and school student/assignment data.
- Full frontend regression suite with bounded workers: 29 files and 170 tests passed.
- Three suites that timed out under unbounded host contention passed independently: 36 tests.
- Production PWA build: passed; main JS gzip 138.55 kB, CSS gzip 24.10 kB.
- Unexpected component errors include component-stack context in development builds only.
- Authenticated live-browser review remains unavailable because the local Django/MySQL connection rejects TLS credentials; no database configuration was changed.
- Commit: `2897357`.

Exit gate:

- [x] Shared primitives have tests.
- [x] Student dashboard, shell and representative parent, counsellor and school-management layouts have responsive contracts for 360px, 768px and desktop.
- [x] Reduced-motion mode disables decorative entry animation.

## 9. Sprint 3 - Pilot framework and combination domain

### Outcome

Smarta Shauri has source-dated pathways, tracks, combinations and school offerings for the five-county pilot.

### Task 3.1 - Create `guidance` app and framework models

Models:

- `FrameworkVersion`
- `PathwayTrack`
- `SubjectCombination`
- `SchoolOffering`

Important fields:

- stable code;
- title/name;
- pathway relationship;
- track relationship;
- three subject relationships;
- description;
- source URL;
- effective date;
- framework version;
- active state.

Tests:

- model constraints;
- exactly three distinct elective subjects;
- unique code per framework version;
- active-version behavior;
- school offering uniqueness.

Verification:

- Guidance model contract: 15 tests passed.
- Affected accounts, students, RIASEC, school-admin and shared-factory regressions: 66 tests passed including the guidance contract.
- Django system check: no issues.
- Guidance migration drift check: no changes detected.
- Full backend run: exceeded the 120-second command window after 57 passing tests with no failure reported; the full-suite baseline remains outstanding.
- Commit: `ea4e7ab`.

### Task 3.2 - Seed the curated pilot catalogue

- [x] Seed the three pathways.
- [x] Seed their current tracks.
- [x] Seed a manageable, presentation-quality set of combinations covering all pathways.
- [x] Include source URL and effective date.
- [x] Seed at least one demonstration school per pilot county.
- [x] Seed representative school offerings.

Recommended presentation catalogue:

- 3-4 STEM combinations across Pure, Applied and Technical tracks.
- 2-3 Social Sciences combinations.
- 2-3 Arts and Sports Science combinations.

Do not claim the curated set is the complete national catalogue.

Verification:

- Curated catalogue: 10 Ministry-coded combinations across seven tracks and all three pathways.
- Presentation distribution: four STEM, three Social Sciences and three Arts & Sports Science combinations.
- Pilot boundary: one clearly labelled synthetic demonstration school in each of Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua; 20 representative offerings cover all 10 combinations.
- Source metadata: current Ministry/KEMIS subject-combination catalogue URL, effective 2026-01-01 and verified 2026-07-30; framework copy states that the set is not the complete national catalogue.
- Guidance seed/model contract: 25 tests passed, including idempotent forward seed and reversible cleanup that preserves unrelated schools.
- Affected accounts, students, RIASEC, school-admin and shared-factory regressions: 76 tests passed including the guidance contract.
- Django system check: no issues.
- Guidance migration drift check: no changes detected.
- Commit: `cce4907`.

### Task 3.3 - Add read APIs

Create:

- `GET /api/v1/guidance/framework/current/`
- `GET /api/v1/guidance/pathways/`
- `GET /api/v1/guidance/combinations/`
- `GET /api/v1/guidance/combinations/{id}/`

Filters:

- pathway;
- track;
- county;
- school;
- search.

Tests:

- public/reference permissions;
- only active framework data;
- filter correctness;
- source metadata;
- query-count sanity.

Verification:

- Guidance API contract: 19 tests passed.
- All four reference endpoints are public even when a stale invalid authentication cookie is present.
- Combination filters cover pathway, track, county, school and search.
- Inactive combinations and records outside the current active framework return no public data.
- Pathway and combination list endpoints remain bounded at three database queries each.
- Combined guidance and RIASEC view regressions: 67 tests passed.
- Django system check: no issues.
- Guidance migration drift check: no changes detected.
- Commit: `9b84c28`.

### Task 3.4 - Add school offerings API

- `GET /api/v1/school-admin/offerings/`
- `PUT /api/v1/school-admin/offerings/`

Acceptance:

- School admin can replace the school's complete offering selection.
- Related arrays use clear replace semantics.
- Only active pilot combinations can be selected.

Verification:

- School-offerings contract: 16 tests passed.
- GET returns only the authenticated administrator's active, current-framework offerings with school and source metadata.
- PUT supports complete replacement and an empty-list clear operation.
- Invalid shapes, duplicates, nonexistent IDs, inactive combinations and combinations from inactive frameworks are rejected without mutation.
- Unauthenticated, unverified, wrong-role, school-less and inactive-school access paths are covered.
- Concurrent replacements serialize on the school row inside an atomic transaction.
- Combined school-management and guidance regression suite: 97 tests passed.
- Django system check: no issues.
- Guidance and school-admin migration drift check: no changes detected.
- Commit: `d7ab5e1`.

### Task 3.5 - Add typed frontend client

Create `frontend/src/api/guidance.ts`.

- [x] Add types for framework, track, combination and offering.
- [x] Add MSW handlers.
- [x] Add React Query keys in one consistent namespace.

Verification:

- Typed guidance client contract: 5 tests passed.
- Client covers current framework, pathways, filtered combination list, combination detail, school offerings and full-replacement updates.
- Framework, track, pathway, exact three-elective combination, school and offering response types match the backend contract.
- All React Query key factories share the `guidance` root namespace.
- Strict TypeScript check: passed.
- Bounded full frontend run: 29 files and 174 tests passed; one dashboard test timed out under worker contention, and its complete 5-test suite passed independently.
- Production PWA bundling transformed 846 modules and generated the application and service-worker files; the host command remained open after successful generation and exceeded its command window.
- Commit: `88f2109`.

Exit gate:

- [x] Seed command/migration is repeatable.
- [x] Public read APIs return source-dated data.
- [x] School offering updates are permission-tested.
- [x] No N+1 query regression in list endpoints.

## 10. Sprint 4 - Complete learner decision-and-plan journey

### Outcome

A learner can move from evidence to an explainable provisional plan.

### Task 4.1 - Add evidence summary endpoint

Create:

- `GET /api/v1/students/evidence-summary/`
- `GET /api/v1/students/grades/summary/`

Return:

- profile completion;
- academic evidence status;
- assessment status/version;
- saved-combination count;
- plan status;
- one calculated next action.

This replaces dashboard request fan-out and per-subject grade queries.

Acceptance:

- Student dashboard loads with a bounded number of requests.
- Endpoint query count is tested.

Verification:

- Learner summary contract: 16 tests passed.
- Evidence summary reports profile completion, academic evidence, assessment state/version slot, saved-combination count, plan status and one calculated next action.
- Next action progresses from profile to grades, assessment and combination exploration as evidence becomes ready.
- Grade summary returns every enrolled subject and all grade records in one response, including a latest-grade snapshot.
- Both endpoints remain bounded at three database queries; the grade query count stays constant with six subjects and twelve records.
- Combined student model/view regression suite: 69 tests passed.
- Django system check: no issues.
- Student migration drift check: no changes detected.
- Commit: `566de40`.

### Task 4.2 - Add grade source and verification

Extend `CBCGrade`:

- `source = learner | school`
- `verified_by`
- `verified_at`

Pilot behavior:

- learner-created record defaults to learner;
- school verification is available through learner detail/admin flow;
- verification changes are audited.

Verification:

- Grade records default to learner provenance, while serializer read-only fields prevent learners from forging school source or verification metadata.
- An active school administrator can verify or remove verification only for an active learner linked to that administrator's active school.
- Verification accepts a strict boolean, is idempotent for unchanged state and records both verification and removal in the system audit log.
- The model enforces paired verifier/timestamp state and grade summaries expose provenance without extra queries.
- Focused grade-verification suite: 16 tests passed.
- Combined grade, student, school-admin and system-admin regression suite: 133 tests passed.
- Django system check: no issues.
- Student and system-admin migration drift checks: no changes detected after normalizing legacy audit-index names.
- Commit: `457c21e`.

### Task 4.3 - Version assessment and explain interest alignment

Extend:

- `RIASECAssessment.instrument_version`
- `Recommendation.algorithm_version`
- explanation snapshot or deterministic explanation service

Frontend:

- user-scoped, expiring assessment draft key;
- pre-assessment purpose/limitations panel;
- result sections for interest profile, pathways to explore, missing evidence and next step.

Acceptance:

- Result never describes a success probability.
- Historical attempt retains its original version.

Verification:

- New attempts persist `riasec-pilot-1.0`; recommendations persist `interest-alignment-1.0` and a stable explanation snapshot.
- History and latest-result APIs return the saved versions, while pre-existing unversioned rows are labelled explicitly during migration.
- Explanations identify the two leading weighted interest dimensions, state the evidence limitations and provide a practical next step without predicting success or placement.
- Assessment drafts are scoped by learner ID, expire after seven days and are removed together on logout without clearing unrelated preferences.
- The pre-assessment screen explains purpose and limitations; results separate stated interests, pathways, missing evidence and the next action.
- Focused backend assessment suite: 51 tests passed.
- Assessment and evidence-summary regression suite: 67 tests passed.
- Broader affected-domain suite reached 135 passing tests; its single outdated summary expectation was corrected and covered by the passing 67-test rerun.
- Focused frontend assessment, draft, PWA and session suite: 41 tests passed.
- Strict TypeScript check: passed.
- Django system check: no issues.
- RIASEC migration drift check: no changes detected.
- Commit: `eee1684`.

### Task 4.4 - Add learner combination choices

Model:

- `LearnerCombinationChoice`
- student;
- combination;
- status: saved/provisional;
- learner reason;
- created/updated timestamp.

API:

- list/create choice;
- remove saved choice;
- set one provisional choice.

Rules:

- maximum three saved combinations;
- only one provisional choice;
- active pilot combinations only.

Verification:

- Authenticated, verified learners can list and save choices, remove saved choices and promote one saved choice to provisional.
- Choice creation is serialized per learner, rejects duplicates and caps the learner's active comparison set at three combinations.
- A conditional database constraint permits only one provisional choice; promoting another choice atomically demotes the previous provisional choice.
- Creation accepts only active combinations in the current framework, while learners cannot read, change or remove another learner's choices.
- Choice payloads include the complete source-dated combination, subjects, pathway track and active school offerings.
- Evidence summary now reports the saved-choice count and provisional state without exceeding its three-query budget.
- Focused learner-choice, model and summary suite: 47 tests passed.
- Affected guidance and student regression suite: 101 tests passed.
- Django system check: no issues.
- Guidance migration drift check: no changes detected.
- Commit: `a9219f2`.

### Task 4.5 - Build explorer

Create:

- `/explore`
- pathway/track filters;
- county/school-offering filter;
- source/date panel;
- combination cards;
- save action;
- empty and error states.

Reuse:

- public pathway content;
- shared cards/status badges;
- React Query;
- existing toast system.

Verification:

- `/explore` is available only in the authenticated learner shell and has route-aware navigation context.
- Learners can filter by pathway, track, any of the five pilot counties, school offering and free-text catalogue search.
- Every result displays its pathway, track, exact three subjects, pilot-school availability and source catalogue code.
- The current framework title, effective date and official source link remain visible above the results.
- Saving uses the learner-choice API, reports the three-choice limit and updates the comparison count immediately.
- Responsive two-column and single-column layouts include accessible loading skeletons, a filter-reset empty state and retryable errors.
- Explorer, guidance-client, shell and root-route suite: 16 tests passed.
- Strict TypeScript check: passed.
- Frontend design pre-flight: visible copy contains no predictive-success language or dash typography; filters are labelled, CTA contrast is preserved, motion respects reduced-motion and mobile collapse is explicit.
- Commit: `3d2db97`.

### Task 4.6 - Build comparison

Create `/compare`.

Compare:

- pathway;
- track;
- three electives;
- interest evidence;
- academic evidence status;
- school offerings in the five counties;
- related routes/careers;
- evidence gaps;
- source date.

Acceptance:

- Comparison works with two or three saved combinations.
- Mobile view uses stacked comparison sections instead of an unreadable table.

Verification:

- `/compare` is available in the learner shell and requires at least two saved combinations, with a direct recovery link to the explorer.
- Two or three choices are compared across pathway, track, three electives, latest interest evidence, academic evidence, five-county school offerings, related routes, evidence gaps and source date.
- Related routes are curated per pilot combination, persisted in the catalogue and returned through the public and learner-choice contracts.
- Learners can promote a compared option to their single provisional choice with mutation feedback.
- The comparison uses responsive evidence sections and never renders a compressed data table on mobile.
- Focused catalogue and learner-choice backend suite: 50 tests passed.
- Comparison, explorer, guidance-client and authenticated-shell frontend suite: 15 tests passed.
- Strict TypeScript check: passed.
- Django system check: no issues.
- Guidance migration drift check: no changes detected.
- Commit: `38836be`.

### Task 4.7 - Add learner plan and milestones

Models:

- `LearnerPlan`
- `PlanMilestone`

API:

- get/update plan;
- create/update/delete milestone.

Frontend `/plan`:

- provisional choice summary;
- learner reason;
- evidence gaps;
- milestone checklist;
- review status;
- next-action card.

Verification:

- `LearnerPlan` binds one learner to their current provisional choice and supports draft, ready-for-review and reviewed states.
- `PlanMilestone` provides ordered, dated checklist items with server-managed completion timestamps.
- Learner-scoped APIs get or update a plan and create, update or delete only that learner's milestones.
- Changing the provisional choice safely repoints an existing plan and returns it to draft; changing a reviewed reason also clears stale review state.
- `/plan` provides provisional-choice context, an editable learner reason, calculated evidence gaps, milestone progress, review readiness and one next action.
- Empty, loading, retryable error and mutation-feedback states are deliberate, with responsive two-column and single-column layouts.
- Focused learner-plan, guidance-model, evidence-summary and learner-choice backend suite: 66 tests passed.
- Learner-plan, comparison and authenticated-shell frontend suite: 9 tests passed.
- Strict TypeScript check: passed.
- Django system check: no issues.
- Guidance migration drift check: no changes detected.
- Commit: `737d96b`.

### Task 4.8 - Refocus student dashboard

Update the lively dashboard:

- hero shows one calculated next action;
- journey steps become Evidence, Interests, Compare and Plan;
- remove misleading pathway donut/percentage if it cannot be relabelled safely;
- replace arbitrary grade trend percentages;
- link every card to a real destination;
- show incomplete/loading/error states deliberately.

Verification:

- The hero displays the evidence-summary API's calculated next action and links directly to its real destination.
- The arbitrary career-journey percentage and progress bar are removed.
- The journey is organized as Evidence, Interests, Compare and Plan, with data-backed status copy and working destinations.
- The interest-pathway card retains advisory language and now links to the pilot explorer.
- The grade trend continues to use canonical CBE levels on a one-to-eight scale rather than invented percentages.
- Essential learner profile, subject, evidence and choice requests have explicit loading, retryable error and complete states.
- The existing responsive rules collapse the overview, journey, insights and support areas to one column for mobile widths, including 360px.
- Dashboard, shell, learner-plan and comparison frontend suite: 14 tests passed.
- Strict TypeScript check: passed.
- Commit: `7b2c62f`.

Exit gate:

- One learner can complete the full flow without direct URL entry.
- All mutations show loading, success and failure feedback.
- Mobile journey works at 360px.
- Focused accessibility checks pass.

## 11. Sprint 5 - Parent support and access

### Outcome

Parent access is learner-approved and the dashboard supports action rather than passive observation.

### Task 5.1 - Extend parent link state

Fields:

- claimed relationship;
- status: invited/pending_learner/active/revoked;
- learner-approved timestamp;
- revoked timestamp.

APIs:

- student access list;
- approve;
- revoke.

Acceptance:

- Parent cannot access child detail until active.
- Learner can see and revoke active links.
- UI states that legal guardian identity is not independently verified in the pilot.

Verification:

- Parent links record claimed relationship, invited/pending/active/revoked state, learner approval time and revocation time.
- Existing links migrate as active while newly accepted parent invitations wait for learner approval.
- Learner-scoped endpoints list access claims, approve pending access and revoke pending or active access with ownership checks and row locking.
- Parent child lists, child detail, PDF reports and assessment notifications require an active link.
- `/access` lets a learner invite a supporter, inspect the claimed relationship, approve or decline requests and revoke active access.
- The learner shell exposes Parent Access without direct URL entry, with explicit loading, retryable error, empty and mutation-feedback states.
- The UI explicitly states that legal guardian identity is not independently verified during the pilot.
- Parent-access, model, parent-view and invitation backend suite: 76 tests passed after the corrected import.
- Focused active-versus-pending report permission suite: 2 tests passed.
- Parent-access, authentication, shell and route frontend suite: 14 tests passed.
- Strict TypeScript check: passed.
- Django system check: no issues.
- Parent migration drift check: no changes detected.
- Commit: `dac4407`.

### Task 5.2 - Redesign parent dashboard

Use shared dashboard primitives.

Show:

- child switcher;
- child's one next action;
- provisional pathway/combination;
- plan progress;
- upcoming milestone;
- conversation prompt;
- report action;
- access status.

Remove:

- unqualified fit percentage;
- confusing empty copy telling all parents to contact the school.

Verification:

- The active-child API returns each learner's rule-based next action, provisional combination, plan state, completed/total milestone counts, upcoming milestone, conversation prompt and access state.
- Evidence, assessment, choice, plan, milestone and counsellor relationships are prefetched for the dashboard summary.
- The unqualified fit percentage is removed from the parent-dashboard contract and interface.
- A child switcher presents one focused learner workspace rather than repeating passive cards for every child.
- The workspace includes one next action, provisional direction, plan progress, upcoming milestone, conversation prompt, report action and learner-approved access state.
- The empty state explains that the learner must approve access and no longer tells all parents to contact a school.
- The two-column support grid collapses to single-column cards on mobile and does not depend on wide rows.
- Parent summary and access backend suite: 34 tests passed.
- Parent dashboard, role dashboard, shared primitives and child-detail frontend suite: 26 tests passed after updating one retired heading assertion.
- Strict TypeScript check: passed.
- Commit: `257b981`.

### Task 5.3 - Redesign child detail

Sections:

- learner-approved summary;
- interest profile;
- academic readiness;
- provisional combination;
- plan milestones;
- parent-visible notes;
- report.

Acceptance:

- [x] Parent sees only approved data.
- [x] All empty/error/loading states are tested.
- [x] Mobile layout does not rely on wide rows.

Verification:

- Child detail remains restricted to active learner-approved links and returns only non-deleted notes explicitly marked parent-visible.
- Academic readiness, provisional choice, plan milestones and parent-visible notes are prefetched and serialized in the approved child summary.
- Child detail uses responsive cards and stacked mobile sections rather than wide rows.
- Parent detail and access backend suite: 35 tests passed.
- Parent child-detail focused frontend suite: 11 tests passed.
- Parent dashboard, child detail, reports and authenticated-shell frontend regression suite: 26 tests passed.
- Strict TypeScript check: passed.
- Diff whitespace check: passed.
- Commit: `681d874`.

## 12. Sprint 6 - Counsellor intervention workflow

### Outcome

Counsellors can identify why a learner needs support, intervene and schedule a follow-up.

### Task 6.1 - Add explicit attention reasons

Backend service derives:

- assessment missing;
- academic evidence missing;
- no saved combination;
- no plan;
- learner requested review;
- follow-up overdue;
- selected combination unavailable at learner's school.

Do not create a predictive risk score.

Tests:

- [x] every reason independently;
- [x] no false flag when complete;
- [x] query-count threshold.

Verification:

- Seven stable attention reasons cover assessment, academic evidence, saved choices, plans, requested review, overdue follow-up and school-offering availability.
- Each reason returns plain-language guidance without a severity, probability or predictive score.
- Counsellor caseload responses expose `needs_attention` and the complete reason list.
- Counsellor stats count learners with any derived reason rather than treating every completed assessment as complete support.
- Attention service and counsellor API suite: 28 tests passed.
- Affected counsellor, learner-summary and guidance backend suite: 75 tests passed.
- Six-learner attention context remains bounded at seven database queries or fewer.
- Strict TypeScript check: passed.
- Commit: `80d27ec`.

### Task 6.2 - Extend notes into pilot interventions

Extend `CounselorNote` or add a narrow related model:

- [x] category;
- [x] action agreed;
- [x] follow-up date;
- [x] status: open/completed;
- [x] learner-visible;
- [x] parent-visible.

Keep safeguarding/private-note behavior separate.

Verification:

- `CounselorIntervention` is separate from confidential `CounselorNote` records.
- Assigned-caseload-only endpoints list, create and update agreed actions and follow-ups.
- Completion status sets or clears a server-managed completion timestamp.
- Learner visibility defaults on for agreed actions; parent visibility remains explicit and defaults off.
- Open past-due interventions feed the existing attention service through an `EXISTS` annotation without increasing the seven-query caseload ceiling.
- Focused intervention and attention suite: 17 tests passed.
- Complete counsellor and parent-access regression suite: 77 tests passed.
- Django system check: no issues.
- Counsellor migration drift check: no changes detected.
- Strict TypeScript check: passed.
- Commit: `6de164d`.

### Task 6.3 - Redesign counsellor dashboard

Show:

- one priority queue;
- reason chips;
- follow-ups due;
- caseload size;
- learner journey completion;
- recent interventions;
- direct actions.

### Task 6.4 - Redesign caseload and learner detail

- responsive list/card view;
- filters by attention reason;
- evidence summary;
- saved/provisional combinations;
- plan;
- intervention timeline;
- set next step/follow-up.

Exit gate:

- Counsellor can complete the presentation intervention without switching to Django admin.
- Learner sees agreed learner-visible action.
- Parent sees only explicitly parent-visible content.

## 13. Sprint 7 - School onboarding, offerings and cohort workflow

### Outcome

School administrators can operate the pilot without relying on shared-code trust.

### Task 7.1 - School-link approval queue

API and UI:

- list pending requests;
- approve;
- reject;
- audit decision;
- notify learner.

Acceptance:

- Shared code creates a pending request.
- Only the learner's school administrator can decide.

### Task 7.2 - Redesign school dashboard

Show:

- pending link requests;
- total approved students;
- unassigned learners;
- counsellor workload;
- evidence completion;
- plans completed;
- review completion;
- school offerings status.

### Task 7.3 - Redesign students and counsellors

- shared responsive data-list component;
- search/filter;
- explicit assignment status;
- bulk assignment where safe;
- useful zero/error states;
- workload counts.

### Task 7.4 - Build school offerings page

- select from active curated combinations;
- group by pathway and track;
- show three subjects;
- save complete offering set;
- show learner impact warning before removal.

### Task 7.5 - Optional CSV import

Implement only after tasks 7.1-7.4 pass.

Minimum safe flow:

1. Download template.
2. Upload CSV.
3. Preview valid/invalid rows.
4. Confirm.
5. Return row-level results.

Do not build Excel, MIS synchronization or background import for the pilot.

Exit gate:

- School admin can approve the demo learner, configure offerings and assign a counsellor.
- Dashboard metrics update.
- Mobile management surfaces remain usable.

## 14. Sprint 8 - System administration and public alignment

### Outcome

The public proposition and pilot administration match the actual system.

### Task 8.1 - Redesign system-admin dashboard

Show:

- learners by five pilot counties;
- active schools;
- verified learners;
- pending school links;
- assignment coverage;
- plans completed;
- recent important audit events;
- framework version/freshness.

### Task 8.2 - Framework catalogue management

P1 minimum:

- read catalogue;
- activate/deactivate combination;
- inspect source metadata.

P2 optional:

- full create/edit forms.

For presentation reliability, seeded migrations/management commands remain the source of truth even if CRUD is shown.

### Task 8.3 - Expand audit events

Add:

- school-link decision;
- parent-link approval/revocation;
- grade verification;
- provisional combination change;
- plan review;
- report download;
- framework activation;
- school offering change.

### Task 8.4 - Align public pages

Update:

- `/pathways` with current tracks and source dates;
- `/how-it-works` with Evidence -> Interests -> Compare -> Plan -> Review;
- `/for-schools` with the actual pilot workflow;
- footer disclaimer and source links;
- all public copy to say five-county pilot where relevant.

Do not redesign public pages again. Extend the current visual system and components.

Exit gate:

- Public claims exactly match implemented pilot capabilities.
- System administrator can explain and monitor the demo.

## 15. Sprint 9 - Reports, accessibility, PWA and presentation hardening

### Outcome

The pilot can be demonstrated repeatedly on desktop and mobile with reliable data and truthful outputs.

### Task 9.1 - Update PDF report

Include:

- evidence sources;
- interest profile;
- interest alignment explanation;
- academic readiness;
- provisional combination;
- milestones;
- framework/algorithm version;
- generated date;
- advisory disclaimer.

Audit every report download.

### Task 9.2 - Limited offline behavior

- cache application shell;
- cache active public framework response by framework version;
- never cache authenticated APIs;
- user-scoped assessment draft with expiry;
- offline banner;
- clear retry for network-required actions.

### Task 9.3 - Accessibility pass

Verify:

- keyboard-only navigation;
- focus order and visible focus;
- landmark/headings;
- labels and error relationships;
- color contrast;
- chart text alternatives;
- reduced motion;
- 200% zoom;
- 360px width;
- meaningful loading and error announcements.

Add automated checks where current tooling permits. Record manual checks in the presentation runbook.

### Task 9.4 - Performance pass

- remove student dashboard request fan-out;
- lazy-load charts and role-heavy pages if necessary;
- compress illustration assets;
- set bundle-size baseline;
- test throttled mobile network;
- ensure first action remains usable while nonessential data loads.

### Task 9.5 - Seed repeatable demonstration data

Create a management command such as:

```powershell
python manage.py seed_pilot_demo
```

Seed:

- one system administrator;
- five schools, one per county;
- one school administrator;
- two counsellors;
- representative learners;
- one parent;
- pathway/track/combination catalogue;
- school offerings;
- grade histories;
- assessment results;
- saved choices;
- one completed plan;
- one learner needing review;
- notifications and audit events.

The command must be idempotent or provide a clearly documented reset path for non-production demo data.

### Task 9.6 - Create presentation runbook

Create:

- `docs/presentation/pilot-demo-runbook.md`
- `docs/presentation/pilot-test-accounts.md` as a local-only/example template without real secrets
- one-page architecture diagram;
- one-page user-flow diagram;
- known limitations/future-work slide content.

Run the complete 12-15 minute demo at least three times from a fresh browser session.

### Final exit gate

```powershell
cd backend
.\venv\Scripts\pytest tests/ -q

cd ..\frontend
npm test
npm run build
```

Additionally:

- [ ] No critical console errors.
- [ ] No failed API requests in the main demo.
- [ ] No private API entries in Cache Storage.
- [ ] Main flow works at 360px and desktop.
- [ ] PDF downloads and contains the correct disclaimer/version.
- [ ] All seeded demo accounts work.
- [ ] Public copy says pilot and does not imply official placement.
- [ ] Presentation runbook completes without database edits.

## 16. Dashboard completion checklist

| Surface | Hero/priority | Metrics | Main workflow | Help/activity | Mobile | Status |
|---|---|---|---|---|---|---|
| Student | One next evidence/plan action | Evidence, interests, choices, plan | Complete learner journey | Counsellor/activity | Required | Pending |
| Parent | Child next action | Plan and milestone progress | Support child | Prompt/report/access | Required | Pending |
| Counsellor | Priority queue | Caseload, overdue, plan completion | Intervention/follow-up | Recent cases | Required | Pending |
| School admin | Pending operational action | Students, assignments, completion | Approve, assign, configure | Activity | Required | Pending |
| System admin | Pilot health warning/action | County/school/user/plan totals | Manage and audit | Framework freshness | Required | Pending |

Each dashboard is complete only when:

- data is real rather than hardcoded;
- loading, error and empty states exist;
- every action links to an implemented route;
- misleading percentages are absent;
- keyboard and mobile behavior are verified;
- its tests pass.

## 17. Presentation cut line

If the deadline becomes tight, preserve a complete narrow flow instead of shipping many partial pages.

### Must keep

1. Sprint 0 baseline.
2. Grade correctness.
3. Private-cache fix.
4. Shared dashboard primitives.
5. Curated framework and combination data.
6. Learner explorer, comparison and plan.
7. One redesigned dashboard for every role.
8. Parent-approved summary.
9. Counsellor attention reason and follow-up.
10. School offerings and link approval.
11. System-admin pilot metrics.
12. Demo seed and runbook.

### Cut first

1. CSV import.
2. Full catalogue CRUD.
3. Advanced cohort charts.
4. Multiple report layouts.
5. Scheduled SMS/email reminder engine.
6. Advanced assessment packs.
7. Appointments.

### Never cut

- Correct educational labels.
- Truthful recommendation language.
- Authenticated-cache safety.
- Role permissions.
- Error/recovery states in the demo path.
- Test/build verification.

## 18. Recommended commit sequence

1. `fix(test): stabilize current dashboard test baseline`
2. `fix(grades): correct CBE performance level ordering`
3. `fix(pwa): exclude authenticated APIs from runtime cache`
4. `fix(auth): require active school and pending membership`
5. `refactor(ui): extract shared role dashboard primitives`
6. `feat(guidance): add pilot framework and combinations`
7. `feat(guidance): expose pilot catalogue and school offerings`
8. `feat(students): add evidence summary and grade provenance`
9. `feat(assessment): explain versioned interest alignment`
10. `feat(guidance): add saved combination comparison`
11. `feat(plans): add learner plan and milestones`
12. `feat(student-ui): complete decision and planning flow`
13. `feat(parent): add learner-approved support workflow`
14. `feat(counselor): add attention reasons and follow-ups`
15. `feat(school-admin): add link approvals and offerings`
16. `feat(system-admin): add pilot health and audit coverage`
17. `feat(reports): add evidence-backed learner plan report`
18. `test(a11y): cover responsive and accessible pilot flows`
19. `feat(demo): add repeatable pilot presentation data`
20. `docs(presentation): add pilot demo runbook`

## 19. Traceability to audit findings

| Audit finding | Planned response |
|---|---|
| Reversed grade labels | Sprint 1.1 |
| Incorrect Grade 10 catalogue | Sprint 1.2 |
| Unsafe authenticated caching | Sprint 1.3 and Sprint 9.2 |
| Inactive/shared school-code trust | Sprint 1.4 and Sprint 7.1 |
| RIASEC percentage overclaim | Sprint 1.5 and Sprint 4.3 |
| Missing tracks/combinations/offerings | Sprint 3 |
| No complete decision flow | Sprint 4 |
| Parent autonomy/access weakness | Sprint 5 |
| Counsellor risk equals incomplete quiz | Sprint 6 |
| Weak school onboarding | Sprint 7 |
| Incomplete audit/governance | Sprint 8 |
| Inconsistent dashboard design | Sprint 2 and Sprints 4-8 |
| PDF lacks evidence/version context | Sprint 9.1 |
| Weak accessibility/error recovery | Sprint 2.3 and Sprint 9.3 |
| Unrepeatable final presentation | Sprint 9.5 and 9.6 |

## 20. Product success criteria for the final project

The implementation should be considered presentation-ready when evaluators can see:

1. A consistent, polished design across public and all role experiences.
2. A learner completing a realistic Senior School exploration workflow.
3. Correct, source-dated Kenyan education terminology and structures.
4. Transparent interest and academic evidence rather than a magic score.
5. A real subject-combination comparison and provisional plan.
6. Parent, counsellor and school collaboration around the same learner plan.
7. Five-county school administration and system oversight.
8. Mobile, accessibility and limited-connectivity considerations.
9. Clear privacy/safeguarding decisions for a pilot handling minors' data.
10. Tests, architecture and repeatable demo data supporting the claims.
