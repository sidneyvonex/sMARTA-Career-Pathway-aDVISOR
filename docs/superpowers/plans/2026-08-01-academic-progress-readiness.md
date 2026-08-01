# Academic Progress and Education Goals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Follow strict TDD for every production behavior.

**Goal:** Build a production-ready Grade 10–12 Academic Progress and Readiness experience with longitudinal evidence, explainable support alerts, improvement targets, school continuity, and exploratory university/programme goals without claiming official CBE admission eligibility.

**Architecture:** Extend the existing students and accounts domains for versioned evidence and longitudinal ownership, add pure deterministic progress selectors, and introduce a bounded tertiary domain for sourced exploration data. Preserve existing API routes and envelopes, deploy additive backend contracts first, then replace the `/grades` experience behind a rollout flag.

**Tech Stack:** Django 5 + Django REST Framework, pytest-django/factory_boy, React 19 + TypeScript, React Query v5, Vitest/RTL/MSW 2, native CSS design system.

## Global Constraints

- Never convert CBC levels into KCSE grades, cluster points, admission probabilities, or unofficial eligibility.
- EE1–BE2 ordinal ranks are visualization aids used only for trend direction; never expose their aggregate as a percentage or admission score.
- Historical KUCCPS information must name its KCSE framework/cycle, source URL, effective date, and historical-reference status.
- Every alert must expose the evidence and deterministic rule that produced it.
- School-verified evidence cannot be silently edited or deleted; verification retains the verifying school.
- All APIs use `{ data, error, message }`, cookie JWT authentication, existing permission classes, and the standard toast catalogue.
- Registration remains limited to Grades 9 and 10; models support Grades 9–12 and activate later catalogues only from authoritative data.
- Authenticated responses are never cached by the service worker.
- Frontend work uses CSS variables, 44px targets, accessible labels, keyboard focus, reduced motion, responsive states, and existing primitives.
- No Codex co-author lines. One logical commit and one task-scoped review gate per task.

---

### Task 1: Record the Safety and Product Contract

**Files:**
- Create: `docs/superpowers/specs/2026-08-01-academic-progress-readiness-design.md`
- Commit: this plan file and the spec

**Produces:** The authoritative design/safety contract used by every later reviewer.

- [x] Write the design spec with product outcome, terminology, non-negotiable safety rules, Grade 10–12 evidence lifecycle, exact alert precedence, education-goal separation, role permissions, error states, accessibility, test acceptance, rollout, and authoritative-source policy.
- [x] Self-review for placeholders, contradictions, ambiguity, and accidental CBC/KCSE conversion.
- [x] Confirm only the intended two docs are staged.
- [x] Commit `docs(progress): define academic readiness design`.

### Task 2: Version Assessment Evidence

**Files:**
- Modify: `backend/students/models.py`, serializers/admin/factories
- Create: students migration and focused model/API tests

**Produces:** `AssessmentFramework`, `PerformanceLevelDefinition`, and additive `CBCGrade` provenance fields.

- [ ] RED: add tests for framework uniqueness/status, ordered level definitions, nullable official ranges/points, raw-score validation, academic grade 9–12, and immutable verifying-school provenance.
- [ ] GREEN: implement models and serializer fields using existing response patterns.
- [ ] Add a data migration that seeds a clearly labelled Senior School pilot framework with EE1–BE2 ranks/descriptions but no KJSEA score ranges, and backfills existing grades without changing their level or verification.
- [ ] Run focused model, serializer, migration, and existing grade-verification tests.
- [ ] Commit `feat(students): version academic assessment evidence`.

### Task 3: Preserve Longitudinal Subject History

**Files:**
- Modify: students/accounts models, serializers, views, API types, tests
- Create: schema/data migration

**Produces:** Grade 9–12-capable models, `Subject.continuity_code`, and archived enrollments.

- [ ] RED: test cross-grade continuity, active-only enrollment listing, `include_history=true`, duplicate-active constraints, archive behavior, and preservation of grade rows.
- [ ] GREEN: add `continuity_code`; add `academic_year`, `is_active`, `ended_at`; expand model grade choices to 9–12 while leaving registration choices at 9–10.
- [ ] Backfill continuity codes deterministically and academic year from earliest evidence year or creation year.
- [ ] Change POST `/remove/` to archive rather than delete; prevent new grade mutations on archived enrollments.
- [ ] Extend frontend types without exposing unavailable Grade 11/12 catalogues.
- [ ] Run focused and existing students/parent/report tests.
- [ ] Commit `feat(students): preserve longitudinal subject history`.

### Task 4: Add Membership History and Safe Transfers

**Files:**
- Modify: accounts, students, school_admin, counselors, notifications, audit code and tests
- Create: membership migration

**Produces:** `StudentSchoolMembership` and transactional transfer APIs.

- [ ] RED: test one active and one pending membership, migration backfill, request validation, authorization, approve/reject behavior, preserved evidence, old assignment deactivation, notifications, and audit events.
- [ ] GREEN: implement membership model, serializers, learner endpoints, and school-admin decision endpoints.
- [ ] On approval, atomically end the old membership, activate the new one, update `StudentProfile.school`, deactivate old counselor assignment, and retain grade history.
- [ ] Lock verified grade edits/deletes; allow verification removal only by the verifying school while membership is active.
- [ ] Preserve compatibility with existing membership request routes or update all consumers atomically.
- [ ] Run focused transfer/verification tests and affected role suites.
- [ ] Commit `feat(accounts): preserve school membership history`.

### Task 5: Add Explainable Progress Assessment

**Files:**
- Create: `backend/students/progress.py` and focused tests
- Modify: students views/urls/serializers and frontend API types/MSW

**Produces:** Pure progress derivation and `GET /api/v1/students/progress/`.

- [ ] RED: table-test every precedence branch, cross-grade ordering, direction, evidence confidence, evidence snapshots, overall severity, and the no-percentage contract.
- [ ] GREEN: group by continuity code and use framework ranks only for comparisons.
- [ ] Implement exact precedence: missing; latest BE support; one non-BE insufficient; two AE/BE support; latest AE or two declines needs attention; latest EE or improving to at least ME2 strong; otherwise ME on track.
- [ ] Return stable rule codes, labels, suggested action, records used, confidence, and admission disclaimer.
- [ ] Optimize queries and add a query-count regression test.
- [ ] Run focused progress/API tests.
- [ ] Commit `feat(students): add explainable progress assessment`.

### Task 6: Add Academic Improvement Goals

**Files:**
- Modify: students models/serializers/views/urls/API types/MSW
- Create: migration and focused backend/frontend tests

**Produces:** `AcademicGoal` and authenticated learner CRUD.

- [ ] RED: test one active goal per continuity code, ownership, target ordering, maintain-or-improve validation, lifecycle transitions, and counsellor read access.
- [ ] GREEN: implement current/target levels, target period/grade, action plan, status, creator, and timestamps.
- [ ] Add learner CRUD under `/api/v1/students/academic-goals/`; counsellors remain read-only and use interventions for support actions.
- [ ] Derive goal readiness from later evidence but require explicit confirmation before achievement.
- [ ] Add standard success/error/loading toasts and MSW handlers.
- [ ] Commit `feat(students): add academic improvement goals`.

### Task 7: Add the Sourced Tertiary Domain and Future Adapter

**Files:**
- Create: bounded `backend/tertiary/` app, migrations, tests, management command
- Modify: config URLs/settings, students education-goal routes, frontend API types/MSW

**Produces:** Sourced institution/programme exploration, learner goals, CSV import, and unavailable official-placement adapter.

- [ ] RED: test catalogue provenance, institution-only/programme goals, one primary plus two alternatives, permissions, filtering, idempotent import, dry-run rollback, malformed source rejection, and absence of eligibility/probability fields.
- [ ] GREEN: implement Institution, Programme, ProgrammeSubjectReference, HistoricalAdmissionReference, and LearnerEducationGoal.
- [ ] Add read endpoints under `/api/v1/tertiary/` and learner goal CRUD under `/api/v1/students/education-goals/`.
- [ ] Implement validated CSV import with explicit source metadata and no runtime scraping.
- [ ] Define the placement evaluator interface; the only implementation returns `official_criteria_unavailable`, source/framework metadata, and explanatory copy.
- [ ] Run focused tertiary and API tests.
- [ ] Commit `feat(tertiary): add sourced education goal catalogue`.
- [ ] Commit the isolated adapter refactor as `refactor(tertiary): isolate future placement evaluation` if it forms a separate logical diff.

### Task 8: Design and Build the Unified My Progress Experience

**Files:**
- Modify: `/grades` page, students API, navigation, MSW, student styles/tests
- Create focused progress/goal components as required by the approved Figma structure

**Produces:** Responsive unified My Progress dashboard behind `academic_progress_v1`.

- [ ] Invoke design-taste-frontend and declare Smarta Shauri dials 6/4/5.
- [ ] Invoke figma:figma-generate-design and produce/confirm the unified dashboard wireframe.
- [ ] Invoke frontend-design before production component work.
- [ ] RED: test summary, grade/year filters, every status, accessible trend fallback, provenance, alerts, target flow, goal preview, empty/loading/error/retry states, flag fallback, keyboard labels, and toast behavior.
- [ ] GREEN: implement with existing React Query/API/primitives/CSS variables and retain the legacy grade history for one release behind the fallback.
- [ ] Verify 360px, tablet, desktop, reduced-motion, and 44px targets.
- [ ] Commit `feat(ui): add learner academic progress dashboard`.

### Task 9: Build the Education Goals Experience

**Files:**
- Create: `/education-goals` page and focused components/tests
- Modify: routes, navigation, tertiary API, MSW, CSS

**Produces:** Institution/programme exploration and goal management.

- [ ] Complete the same mandatory design-skill sequence before the new page.
- [ ] RED: test institution-only and programme goals, primary/alternative limits, filtering, historical labels, source dates, subject references, official-criteria-unavailable state, API failures, and toasts.
- [ ] GREEN: implement search, detail, goal actions, progress cross-links, loading/empty/error states, and responsive accessibility.
- [ ] Never render eligible/ineligible, a probability, a CBC admission score, or an unlabeled historical cutoff.
- [ ] Commit `feat(ui): add exploratory education goals`.

### Task 10: Integrate Supporting Roles, Reports, and Notifications

**Files:**
- Modify: counselor/parent/school-admin/system-admin APIs and pages, reports, notifications, demo seed, tests

**Produces:** Permission-safe cross-role support for the same progress evidence.

- [ ] RED: add role-specific API/UI tests for visible fields and forbidden private data.
- [ ] Show counsellors progress explanations, targets, goals, and academic-evidence intervention action.
- [ ] Show approved parents read-only learner-approved progress/goals without private notes.
- [ ] Show school admins memberships, transfers, provenance, and valid verification controls.
- [ ] Show system admins assessment-framework and tertiary-source metadata management.
- [ ] Extend reports with progress, provenance, targets, goals, framework version, generated date, and advisory disclaimer.
- [ ] Add notifications for verification, transfer decisions, interventions, and confirmed goal achievement.
- [ ] Update repeatable demo seed and run affected role/report suites.
- [ ] Commit each independently reviewable role/report slice using the project commit format.

### Task 11: Full Verification, Review, and Branch Finish

**Files:** No new product scope.

- [ ] Run backend migrations/checks and the complete backend suite.
- [ ] Run complete frontend tests and production build with pristine output.
- [ ] Execute the seeded learner journey: evidence → alert → target → education goal → counsellor action → school transfer.
- [ ] Invoke coderabbit:code-review for the whole branch and resolve validated findings.
- [ ] Invoke verification-before-completion and record exact command evidence.
- [ ] Invoke finishing-a-development-branch and present integration options without force-pushing or merging automatically.
