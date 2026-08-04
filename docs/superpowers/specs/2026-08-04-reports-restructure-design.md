# Reports Restructure Design Specification

**Date:** 4 August 2026  
**Status:** Approved for implementation  
**Scope:** PDF report architecture, six role-level reports, and dashboard download actions

## 1. Purpose

Extend Smarta Shauri's reporting beyond the existing student progress PDF without turning `reports/pdf_builder.py` into a large, duplicated report engine. The work preserves the student report's content while extracting a shared PDF theme and reusable components, then adds school, counsellor, and platform reports with strictly scoped data.

## 2. PDF architecture

Replace the monolithic builder with a package:

```text
backend/reports/pdf/
  __init__.py
  theme.py
  components.py
  student.py
  cohort.py
  platform.py
```

- `theme.py` owns brand colours and the shared ReportLab style sheet.
- `components.py` owns reusable flowable builders: `report_header`, `section_title`, `key_value_table`, `data_table`, `stat_grid`, `empty_state`, and `footer_disclaimer`.
- `student.py` contains the existing `build_student_report(data)` behavior, refactored to consume shared theme/components.
- `cohort.py` contains the school and counsellor overview/roster builders. Both roles use the same rendering path because they differ only in scope, title, and whether the assigned-counsellor column is useful.
- `platform.py` contains the system-wide overview and schools-directory builders.
- `reports/pdf/__init__.py` exports the public builder functions used by views and tests.

The student report refactor is content-preserving. It is not a content or visual redesign.

## 3. Shared PDF components

- `report_header(title, subtitle, generated_at, logo_path)` renders the optional logo, report title, context subtitle, and generation date.
- `section_title(text)` renders the standard forest-green section heading.
- `key_value_table(rows, col_widths)` renders two-column labelled facts.
- `data_table(headers, rows, col_widths, highlight_row_indices=None)` renders a branded header, zebra striping, wrapping, and optional highlighted rows.
- `stat_grid(stats)` renders two or three columns of labelled metrics with optional sublabels.
- `empty_state(message)` renders one consistent no-data treatment.
- `footer_disclaimer(text)` renders the advisory-only disclaimer block.

All dynamic strings must be XML-escaped before they reach ReportLab paragraphs. Wide and long tables must repeat their header row and be allowed to split across pages.

## 4. Reports and endpoints

All endpoints use `APIView`, `IsAuthenticated`, `IsEmailVerified`, the applicable role permission, an `application/pdf` response, attachment `Content-Disposition`, and `log_action()`.

| Endpoint | Permission | Output |
|---|---|---|
| `GET /api/v1/reports/school/overview/pdf/` | `IsSchoolAdmin` | School summary metrics and counsellor workload |
| `GET /api/v1/reports/school/roster/pdf/?grade=10` | `IsSchoolAdmin` | Active learners at the requester's school |
| `GET /api/v1/reports/counselor/overview/pdf/` | `IsCounselor` | Metrics for the requester's active assignments |
| `GET /api/v1/reports/counselor/roster/pdf/?grade=10` | `IsCounselor` | Learners actively assigned to the requester |
| `GET /api/v1/reports/system/overview/pdf/` | `IsSystemAdmin` | Platform rollout and completion metrics |
| `GET /api/v1/reports/system/schools/pdf/` | `IsSystemAdmin` | School directory with learner/counsellor counts |

Roster columns are: learner name, grade, RIASEC status, subjects enrolled, subjects with evidence, plan status, and—only for the school report—assigned counsellor.

## 5. Query and service design

Shared statistics belong outside HTTP views:

- Extract `school_admin.reporting.get_school_stats(school)` from `SchoolStatsView`; both JSON and PDF consumers call it.
- Extract `system_admin.reporting.get_platform_stats()` from `DashboardView`; both JSON and PDF consumers call it.
- Add `counselors.reporting.get_caseload_stats(counselor)`, based on active `CounselorAssignment` rows and the existing counsellor dashboard semantics. The helper may add report-specific evidence, choice, and plan coverage fields while preserving the current JSON response contract.
- Add roster selector helpers that return already-scoped, efficiently related/prefetched learner records. Rendering code must not query the database.

Scope is always derived from the authenticated user. No school or counsellor identifier is accepted from the client.

## 6. Request and response behavior

- A school admin without a school receives the existing 404 message: `No school assigned to your account.`
- `grade` is optional and validated against `GRADE_LEVEL_CHOICES`. Invalid input returns `_error('Invalid grade filter.', 400)`.
- An empty cohort generates a valid PDF and displays `No learners match this filter.`
- Standard permission failures remain DRF 403 responses.
- Filenames follow `smarta-shauri-<report-type>-<scope>-<date>.pdf` and are sanitized for header safety.
- Each successful download creates a `report_downloaded` audit event with `report_type`, optional `grade_filter`, and `requester_role` in `details`. The target is the school for school reports, the counsellor for caseload reports, and `0` for platform reports.

## 7. Frontend design

Extend `frontend/src/api/reports.ts` with one typed function per endpoint. All requests use the shared Axios client and `responseType: 'blob'`.

Generalize `useDownloadReport` to accept an arbitrary PDF request function and fallback filename. It remains the single owner of blob creation, filename extraction, object-URL cleanup, loading state, and success/error toasts. Existing student report call sites receive a signature-only update.

Add download actions to existing dashboards:

- School admin: school overview and learner roster, with an optional grade filter.
- Counsellor: caseload overview and caseload roster, with an optional grade filter.
- System admin: platform overview and schools directory.

These are additions to established dashboard sections, not new pages. Controls use existing dashboard/card/button styles, include accessible labels, and disable while their download is in progress.

## 8. Testing

Backend coverage includes:

- Student PDF regression coverage after the package refactor.
- Correct permission gates for every endpoint.
- School and counsellor scope isolation.
- Valid, invalid, and empty grade-filter behavior.
- Report data shaping and PDF content type/disposition.
- `report_downloaded` audit details.
- Bounded query counts for roster growth where practical.

Frontend coverage includes:

- MSW handlers for all six endpoints.
- Each dashboard action calling the correct endpoint.
- Grade filter forwarding for both roster variants.
- Loading/disabled behavior, filename handling, and success/error toasts.
- Existing student download behavior after the hook generalization.

## 9. Delivery phases

1. Refactor the PDF builder package and prove student report parity.
2. Extract school reporting queries and add school PDFs.
3. Add counsellor reporting helpers and PDFs.
4. Extract platform reporting queries and add system PDFs.
5. Generalize frontend downloading and add dashboard actions.
6. Run focused and full regression suites, review the diff, and update documentation.

## 10. Acceptance criteria

- The existing student report remains downloadable with its current sections and data.
- All six new endpoints enforce the correct role and data scope.
- Empty cohorts generate readable PDFs instead of errors.
- Statistics shown in JSON dashboards and corresponding PDFs come from the same helpers.
- All downloads are audited with a distinguishable `report_type`.
- Dashboard controls work at supported viewport sizes and expose clear loading state.
- Backend and frontend report tests pass, followed by the complete project test suites.

## 11. Out of scope

- Scheduled or emailed reports.
- CSV/Excel exports.
- User-configurable report templates.
- New predictive scores or risk classifications.
- Changing the student report's substantive content.
