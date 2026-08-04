# Reports Restructure — Implementation Plan

> Execute tasks in order. Use test-driven development, run focused tests after each task, and keep unrelated working-tree changes untouched.

**Goal:** Deliver a maintainable shared PDF system plus six scoped administrative reports and dashboard download actions.

**Architecture:** ReportLab rendering lives in `reports/pdf/`; database aggregation lives in role-owned `reporting.py` helpers; `reports/views.py` only resolves request scope, shapes data, renders PDFs, audits successful downloads, and returns responses.

**Tech stack:** Django 4.2, Django REST Framework, ReportLab, pytest-django, factory_boy, React 18, TypeScript, Axios, Vitest, React Testing Library, MSW 2.

## Global constraints

- Preserve the current student PDF's content and public import.
- Derive report scope exclusively from `request.user`.
- Use factories in backend tests and the shared Axios client in frontend code.
- Validate `grade` against `StudentProfile.GRADE_CHOICES`.
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

- [x] Add regression tests for the public builder import, `%PDF` output, optional logo, empty sections, and escaped dynamic text.
- [x] Move brand constants/styles into `theme.py`.
- [x] Implement shared component builders.
- [x] Move `build_student_report` into `student.py` and replace repeated table/heading/empty-state code where behavior remains equivalent.
- [x] Export `build_student_report` from `reports.pdf` and update imports.
- [x] Run `pytest tests/test_reports.py -v` (42 passed).
- [x] Commit as `refactor(reports): extract shared PDF package`.

## Task 2: School reporting services and PDFs

**Files:**

- Create `backend/school_admin/reporting.py`
- Modify `backend/school_admin/views.py`
- Create `backend/reports/pdf/cohort.py`
- Modify `backend/reports/pdf/__init__.py`
- Modify `backend/reports/views.py`
- Modify `backend/reports/urls.py`
- Modify `backend/tests/test_reports.py`

- [x] Write tests for school overview/roster permissions, missing school, scope isolation, grade filtering, empty results, filenames, and audit details.
- [x] Extract `get_school_stats(school)` without changing the JSON dashboard contract.
- [x] Add a school roster selector with related/prefetched evidence, assessment, choice/plan, and assignment data.
- [x] Implement shared cohort overview and roster renderers.
- [x] Implement school report views and routes.
- [x] Run school-admin and report test modules.
- [ ] Commit as `feat(reports): add school overview and roster PDFs`.

## Task 3: Counsellor reporting services and PDFs

**Files:**

- Create `backend/counselors/reporting.py`
- Modify the existing counsellor stats view to consume the helper if contracts align
- Modify `backend/reports/views.py`
- Modify `backend/reports/urls.py`
- Modify `backend/tests/test_reports.py`

- [x] Write tests for role permission, active-assignment isolation, valid/invalid/empty grade filters, filenames, and audit details.
- [x] Implement `get_caseload_stats(counselor)` using active assignments and existing dashboard semantics.
- [x] Add a counsellor roster selector using the same learner row shaping as school reports and omit the redundant counsellor column.
- [x] Implement counsellor report views and routes.
- [x] Run counsellor and report test modules.
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

- [x] Write tests for system-admin-only access, overview data, directory rows, filenames, and audit details.
- [x] Extract `get_platform_stats()` without changing the JSON dashboard contract.
- [x] Add an annotated schools-directory selector.
- [x] Implement platform overview and schools-directory renderers.
- [x] Implement system report views and routes.
- [x] Run system-admin and report test modules.
- [ ] Commit as `feat(reports): add platform overview and schools PDFs`.

## Task 5: Generalize frontend downloads

**Files:**

- Modify `frontend/src/api/reports.ts`
- Modify `frontend/src/hooks/useDownloadReport.ts`
- Modify existing student-report call sites
- Modify `frontend/src/test/reports/Reports.test.tsx`
- Modify `frontend/src/test/msw/handlers.ts`

- [x] Add hook/API coverage for the shared downloader and role report actions.
- [x] Add typed API functions for all six endpoints.
- [x] Generalize the hook while preserving existing student behavior.
- [x] Add MSW handlers for all report endpoints.
- [x] Run the focused report tests; TypeScript reaches an unrelated upload-interceptor error in `src/lib/axios.ts`.
- [ ] Commit as `refactor(reports): generalize frontend PDF downloads`.

## Task 6: Add dashboard report actions

**Files:**

- Modify `frontend/src/components/dashboard/admin/SchoolAdminDashboard.tsx`
- Modify `frontend/src/components/dashboard/counselor/CounselorDashboard.tsx`
- Modify `frontend/src/components/system-admin/SystemAdminDashboard.tsx`
- Modify relevant dashboard/report tests and existing dashboard styles only if needed

- [x] Write tests for report actions and school grade forwarding.
- [x] Add school overview/roster controls and an accessible all-grades/default selector.
- [x] Add counsellor overview/roster controls and selector.
- [x] Add platform overview/schools-directory controls.
- [x] Reuse existing dashboard patterns and CSS variables.
- [x] Run focused frontend tests; production build is blocked by the unrelated Axios type error noted above.
- [ ] Commit as `feat(reports): add role dashboard download actions`.

## Task 7: Full verification and review

- [x] Run all backend tests (five unrelated snapshot-checksum failures; touched modules pass).
- [x] Run all frontend tests (pass); production build remains blocked by the unrelated Axios type error.
- [x] Smoke-test generated samples for all four builder paths, including cohort/platform tables.
- [x] Review scope filters, permission gates, content-disposition safety, URL cleanup, and accessibility.
- [ ] Resolve findings and rerun affected/full suites.
- [ ] Confirm `git diff` excludes unrelated pre-existing changes.
- [ ] Commit any review fixes separately with an appropriate conventional commit message.
