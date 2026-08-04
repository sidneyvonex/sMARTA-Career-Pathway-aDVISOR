# Reports Restructure — Implementation Plan

> Execute tasks in order. Use test-driven development, run focused tests after each task, and keep unrelated working-tree changes untouched.

**Goal:** Deliver a maintainable shared PDF system plus six scoped administrative reports and dashboard download actions.

**Architecture:** ReportLab rendering lives in `reports/pdf/`; database aggregation lives in role-owned `reporting.py` helpers; `reports/views.py` only resolves request scope, shapes data, renders PDFs, audits successful downloads, and returns responses.

**Tech stack:** Django 4.2, Django REST Framework, ReportLab, pytest-django, factory_boy, React 18, TypeScript, Axios, Vitest, React Testing Library, MSW 2.

## Global constraints

- Preserve the current student PDF's content and public import.
- Derive report scope exclusively from `request.user`.
- Use factories in backend tests and the shared Axios client in frontend code.
- Validate `grade` against `GRADE_LEVEL_CHOICES`.
- Escape all dynamic ReportLab paragraph content.
- Keep PDF builders database-free.
- Reuse `_error`, role permission classes, and `log_action`.
- Do not modify or stage unrelated worktree changes.

## Task 1: Extract the PDF package with student parity

**Files:**

- Create `backend/reports/pdf/__init__.py`
- Create `backend/reports/pdf/theme.py`
- Create `backend/reports/pdf/components.py`
- Create `backend/reports/pdf/student.py`
- Modify `backend/reports/views.py`
- Remove `backend/reports/pdf_builder.py` after imports are migrated
- Modify `backend/tests/test_reports.py`

- [ ] Add regression tests for the public builder import, `%PDF` output, optional logo, empty sections, and escaped dynamic text.
- [ ] Move brand constants/styles into `theme.py`.
- [ ] Implement shared component builders.
- [ ] Move `build_student_report` into `student.py` and replace repeated table/heading/empty-state code where behavior remains equivalent.
- [ ] Export `build_student_report` from `reports.pdf` and update imports.
- [ ] Run `pytest tests/test_reports.py -v`.
- [ ] Commit as `refactor(reports): extract shared PDF package`.

## Task 2: School reporting services and PDFs

**Files:**

- Create `backend/school_admin/reporting.py`
- Modify `backend/school_admin/views.py`
- Create `backend/reports/pdf/cohort.py`
- Modify `backend/reports/pdf/__init__.py`
- Modify `backend/reports/views.py`
- Modify `backend/reports/urls.py`
- Modify `backend/tests/test_reports.py`

- [ ] Write failing tests for school overview/roster permissions, missing school, scope isolation, grade filtering, empty results, filenames, and audit details.
- [ ] Extract `get_school_stats(school)` without changing the JSON dashboard contract.
- [ ] Add a school roster selector with related/prefetched evidence, assessment, choice/plan, and assignment data.
- [ ] Implement shared cohort overview and roster renderers.
- [ ] Implement school report views and routes.
- [ ] Run school-admin and report test modules.
- [ ] Commit as `feat(reports): add school overview and roster PDFs`.

## Task 3: Counsellor reporting services and PDFs

**Files:**

- Create `backend/counselors/reporting.py`
- Modify the existing counsellor stats view to consume the helper if contracts align
- Modify `backend/reports/views.py`
- Modify `backend/reports/urls.py`
- Modify `backend/tests/test_reports.py`

- [ ] Write failing tests for role permission, active-assignment isolation, valid/invalid/empty grade filters, filenames, and audit details.
- [ ] Implement `get_caseload_stats(counselor)` using active assignments and existing dashboard semantics.
- [ ] Add a counsellor roster selector using the same learner row shaping as school reports and omit the redundant counsellor column.
- [ ] Implement counsellor report views and routes.
- [ ] Run counsellor and report test modules.
- [ ] Commit as `feat(reports): add counsellor overview and roster PDFs`.

## Task 4: Platform reporting services and PDFs

**Files:**

- Create `backend/system_admin/reporting.py`
- Modify `backend/system_admin/views.py`
- Create `backend/reports/pdf/platform.py`
- Modify `backend/reports/pdf/__init__.py`
- Modify `backend/reports/views.py`
- Modify `backend/reports/urls.py`
- Modify `backend/tests/test_reports.py`

- [ ] Write failing tests for system-admin-only access, overview data, directory rows, filenames, and audit details.
- [ ] Extract `get_platform_stats()` without changing the JSON dashboard contract.
- [ ] Add an annotated schools-directory selector.
- [ ] Implement platform overview and schools-directory renderers.
- [ ] Implement system report views and routes.
- [ ] Run system-admin and report test modules.
- [ ] Commit as `feat(reports): add platform overview and schools PDFs`.

## Task 5: Generalize frontend downloads

**Files:**

- Modify `frontend/src/api/reports.ts`
- Modify `frontend/src/hooks/useDownloadReport.ts`
- Modify existing student-report call sites
- Modify `frontend/src/test/reports/Reports.test.tsx`
- Modify `frontend/src/test/msw/handlers.ts`

- [ ] Add failing hook/API tests for an arbitrary fetcher, fallback/server filename, cleanup, errors, and concurrent button state.
- [ ] Add typed API functions for all six endpoints.
- [ ] Generalize the hook while preserving existing student behavior.
- [ ] Add MSW handlers for all report endpoints.
- [ ] Run the focused report tests and TypeScript check.
- [ ] Commit as `refactor(reports): generalize frontend PDF downloads`.

## Task 6: Add dashboard report actions

**Files:**

- Modify `frontend/src/components/dashboard/admin/SchoolAdminDashboard.tsx`
- Modify `frontend/src/components/dashboard/counselor/CounselorDashboard.tsx`
- Modify `frontend/src/components/system-admin/SystemAdminDashboard.tsx`
- Modify relevant dashboard/report tests and existing dashboard styles only if needed

- [ ] Write failing tests for each report action, grade forwarding, and disabled state.
- [ ] Add school overview/roster controls and an accessible all-grades/default selector.
- [ ] Add counsellor overview/roster controls and selector.
- [ ] Add platform overview/schools-directory controls.
- [ ] Reuse existing dashboard patterns and CSS variables.
- [ ] Run focused frontend tests and the production build.
- [ ] Commit as `feat(reports): add role dashboard download actions`.

## Task 7: Full verification and review

- [ ] Run all backend tests.
- [ ] Run all frontend tests and the production build.
- [ ] Inspect generated samples for each of the seven PDF types, including multi-page rosters and empty cohorts.
- [ ] Review scope filters, query counts, permission gates, content-disposition safety, URL cleanup, and accessibility.
- [ ] Resolve findings and rerun affected/full suites.
- [ ] Confirm `git diff` excludes unrelated pre-existing changes.
- [ ] Commit any review fixes separately with an appropriate conventional commit message.
