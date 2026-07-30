# Smarta Shauri Five-County Pilot Execution Plan

**Date:** 2026-07-30  
**Specification:** `docs/superpowers/specs/2026-07-30-pilot-product-spec.md`  
**Execution style:** Sequential vertical slices, test-first, one logical commit per task  
**Target:** Final-project presentation pilot, not national production release

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

- [ ] Review `git diff --stat` and `git diff`.
- [ ] Separate public/student redesign files from unrelated changes.
- [ ] Confirm no generated PDF or local design artifacts will be included in a product-code commit.
- [ ] Record the current visual baseline at desktop, tablet and 360px mobile.

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

- [ ] Diagnose the parent dashboard timeout.
- [ ] Diagnose the school-admin loading/assertion failure.
- [ ] Remove material `act()` warnings in affected tests.
- [ ] Keep MSW data aligned with the current dashboard contracts.

Acceptance:

- `npm test` passes.
- No test depends on arbitrary delays.

### Task 0.3 - Establish quality baseline

- [ ] Run backend tests.
- [ ] Run frontend tests.
- [ ] Run frontend production build.
- [ ] Record baseline bundle sizes and known warnings.
- [ ] Confirm the five pilot counties remain unchanged.

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

- [ ] Correct labels so Level 1 is higher than Level 2 in each band.
- [ ] Define one canonical ordering utility in backend and frontend.
- [ ] Remove arbitrary dashboard percentage conversion.
- [ ] Display trends as ordered performance bands or clearly labelled points.
- [ ] Update report labels and test fixtures.

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

- [ ] Keep Grade 9 learning areas required by the pilot.
- [ ] Replace duplicate junior-style Grade 10 seed data with current Senior School core/elective names needed by the curated pilot combinations.
- [ ] Preserve existing student records safely through a forward data migration.
- [ ] Mark obsolete seeded subjects inactive rather than deleting referenced rows.

Acceptance:

- Grade 10 selection does not show Integrated Science/Social Studies as a duplicated junior catalogue.
- Every seeded combination in Sprint 3 can resolve its subjects.

### Task 1.3 - Stop caching authenticated API data

Files:

- `frontend/vite.config.ts`
- `frontend/src/hooks/usePWAUpdate.tsx`
- `frontend/src/test/pwa/PWA.test.tsx`

Work:

- [ ] Remove the broad `/api/v1/` `StaleWhileRevalidate` rule.
- [ ] Cache only explicitly public framework endpoints later.
- [ ] Version the cache name.
- [ ] Remove legacy private API caches during service-worker activation.
- [ ] Clear user-scoped local drafts on logout where appropriate.

Acceptance:

- Authenticated student, parent, counsellor and admin responses are never served from Workbox cache.
- A test proves the private route pattern is excluded.

### Task 1.4 - Validate active school joins

Files:

- `backend/accounts/serializers.py`
- `backend/accounts/views.py`
- `backend/tests/test_accounts_views.py`

Work:

- [ ] Reject inactive school codes.
- [ ] Store school-linked registration as pending approval rather than silently trusted.
- [ ] Preserve self-guided registration.

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

- [ ] Replace "fit percentage" presentation with "interest alignment."
- [ ] Add a clear advisory explanation.
- [ ] Remove placement/success implications.
- [ ] Keep the numeric value internal only if needed for ranking during the pilot.

Exit gate:

- Focused backend/frontend tests pass.
- Production build passes.
- Manual shared-device PWA check passes.
- Correct terminology appears in learner, parent, counsellor and PDF surfaces.

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

- [ ] Extract stable concepts from `lively/*`.
- [ ] Accept role-specific color/accent variants through props/classes.
- [ ] Keep visual tokens in `theme.css`.
- [ ] Remove hardcoded inline layout/color styles from migrated areas.
- [ ] Add component tests for interactive behavior and accessibility labels.

Acceptance:

- Student dashboard still looks intentional after extraction.
- At least parent and counsellor prototypes can render using the same primitives.

### Task 2.2 - Standardize authenticated page layout

Files:

- `frontend/src/components/shell/Shell.tsx`
- `Sidebar.tsx`
- `Topbar.tsx`
- `frontend/src/styles/shell.css`
- new `frontend/src/styles/role-dashboard.css`

Work:

- [ ] Define common content width, page spacing and responsive breakpoints.
- [ ] Add consistent page title/breadcrumb/action positions.
- [ ] Add mobile navigation behavior for all roles.
- [ ] Add global offline indicator placeholder.
- [ ] Ensure notification and profile actions remain reachable at 360px.

### Task 2.3 - Route error and recovery boundary

- [ ] Add application/route error boundary.
- [ ] Add reusable retry state.
- [ ] Ensure query errors do not leave blank screens.
- [ ] Log unexpected frontend errors in development.

Exit gate:

- Shared primitives have tests.
- Student dashboard, shell and at least two representative management pages work at 360px, 768px and desktop.
- Reduced-motion mode disables decorative entry animation.

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

### Task 3.2 - Seed the curated pilot catalogue

- [ ] Seed the three pathways.
- [ ] Seed their current tracks.
- [ ] Seed a manageable, presentation-quality set of combinations covering all pathways.
- [ ] Include source URL and effective date.
- [ ] Seed at least one demonstration school per pilot county.
- [ ] Seed representative school offerings.

Recommended presentation catalogue:

- 3-4 STEM combinations across Pure, Applied and Technical tracks.
- 2-3 Social Sciences combinations.
- 2-3 Arts and Sports Science combinations.

Do not claim the curated set is the complete national catalogue.

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

### Task 3.4 - Add school offerings API

- `GET /api/v1/school-admin/offerings/`
- `PUT /api/v1/school-admin/offerings/`

Acceptance:

- School admin can replace the school's complete offering selection.
- Related arrays use clear replace semantics.
- Only active pilot combinations can be selected.

### Task 3.5 - Add typed frontend client

Create `frontend/src/api/guidance.ts`.

- [ ] Add types for framework, track, combination and offering.
- [ ] Add MSW handlers.
- [ ] Add React Query keys in one consistent namespace.

Exit gate:

- Seed command/migration is repeatable.
- Public read APIs return source-dated data.
- School offering updates are permission-tested.
- No N+1 query regression in list endpoints.

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

### Task 4.2 - Add grade source and verification

Extend `CBCGrade`:

- `source = learner | school`
- `verified_by`
- `verified_at`

Pilot behavior:

- learner-created record defaults to learner;
- school verification is available through learner detail/admin flow;
- verification changes are audited.

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

### Task 4.8 - Refocus student dashboard

Update the lively dashboard:

- hero shows one calculated next action;
- journey steps become Evidence, Interests, Compare and Plan;
- remove misleading pathway donut/percentage if it cannot be relabelled safely;
- replace arbitrary grade trend percentages;
- link every card to a real destination;
- show incomplete/loading/error states deliberately.

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

- Parent sees only approved data.
- All empty/error/loading states are tested.
- Mobile layout does not rely on wide rows.

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

- every reason independently;
- no false flag when complete;
- query-count threshold.

### Task 6.2 - Extend notes into pilot interventions

Extend `CounselorNote` or add a narrow related model:

- category;
- action agreed;
- follow-up date;
- status: open/completed;
- learner-visible;
- parent-visible.

Keep safeguarding/private-note behavior separate.

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
