# Code Audit

**Baseline:** `origin/main` at `65fd088f9af97fddaea208796aca265ae9310c70`
**Status:** Data and public-contract remediation complete; production rollout and full-suite performance remain open

| ID | Severity | Area | Finding | Evidence | User impact | Recommendation | Verification |
|---|---|---|---|---|---|---|---|
| AUD-CODE-001 | High | Data integrity | A production data migration created five synthetic schools with `PILOT-*` codes and assigned curated offerings. The public combination API previously serialized these schools as ordinary availability. | `backend/guidance/migrations/0002_seed_pilot_catalogue.py:130`; `backend/guidance/selectors.py`; `backend/guidance/migrations/0006_catalogue_provenance.py` | A learner or parent could interpret demonstration offerings as verified real-school availability. | Implemented: synthetic schools and offerings are classified as `demonstration`; only verified schools and offerings can enter public guidance responses and filters. | `FIXED`; API regression suite verified 2026-07-31. |
| AUD-CODE-002 | High | Provenance | Provenance previously existed only at framework level. `School`, `SubjectCombination` and `SchoolOffering` did not store per-record source, checked date or verification status. | Provenance migrations; official identity/offering fetch and import commands; system-admin evidence columns. | The application could not prove which school offering was checked, when it was checked or whether it was official. | Implemented: checksum-pinned, dry-run-first imports; per-record provenance; exact identity matching; quarantine; public verification gates; administrative evidence visibility. | `FIXED`; 1,253 identities and 623 offerings validated and imported locally on 2026-07-31. Production import remains a deployment operation. |
| AUD-CODE-003 | Medium | Guidance algorithm | The backend calculated, stored and exposed a numeric `fit_pct` through assessment, counsellor, parent and report contracts. | `backend/riasec/serializers.py`; `backend/counselors/views.py`; `backend/reports/views.py`; frontend API types. | A percentage could be mistaken for eligibility, success probability or placement likelihood. | Keep internal score snapshots for reproducibility, but expose only rank, qualitative alignment and explanation. | `FIXED`; numeric fit fields removed from public and role-facing contracts and the production build passes. |
| AUD-CODE-004 | Medium | Rollout scope | The same five counties were repeated across frontend forms and described in places as though they might be an official pilot designation. | `frontend/src/lib/rollout.ts`; backend `COUNTY_CHOICES`; public and administration wording. | Future scope changes required coordinated edits, and users could infer an unsupported Ministry pilot designation. | Treat the list explicitly as current project rollout scope and centralize shared options. | `MITIGATED`; frontend duplication removed and wording corrected. Backend remains intentionally county-limited pending a future national-scope product decision. |
| AUD-CODE-005 | High | Subject catalogue | Grade 10 Core/Essential Mathematics were stored as `Elective`, while Physical Education was stored as `Core`. KICD’s December 2025 Grade 10 addendum defines English, Kiswahili/KSL, Core or Essential Mathematics and CSL as the four core learning areas, with Physical Education scheduled separately. | `backend/students/migrations/0005_correct_grade10_catalogue.py:9`; KICD Grade 10 addendum checked 2026-07-31 | Learners, reports and eligibility logic could present the wrong core/elective classification. The combination validator also depended on Mathematics being labelled elective, so a direct data edit would have broken valid combinations. | Implemented: curriculum category is now separate from combination selectability, and a data migration corrects Mathematics and Physical Education without invalidating official combinations. | `FIXED`; migration and regression suite verified 2026-07-31. |

## Architecture inventory

| Layer | Current implementation | Audit focus |
|---|---|---|
| Backend | Django 4.2 and Django REST Framework | Permissions, provenance, validation, catalogue integrity and role-specific exposure |
| Frontend | React 18, TypeScript, React Query and Vite | Content claims, flow parity, accessibility, offline behavior and error recovery |
| Guidance data | Django migrations and database models | Synthetic versus official data, source metadata and lifecycle/versioning |
| Interest guidance | 30-question RIASEC assessment with weighted pathway ranking | Non-predictive explanation, algorithm transparency and percentage exposure |
| Tests | 36 backend test modules and 36 frontend test files | Full baseline, domain-rule regression tests and inherited-finding reproduction |

## Test baseline

- Frontend production build: **passed** on 2026-07-31.
- Focused backend guidance/catalogue/model suite: **89 passed** on 2026-07-31.
- Focused frontend guidance/content regression suite: **42 passed** on 2026-07-31.
- Backend full suite: no failure appeared before the expanded 300-second command
  window expired at 11% completion. Three parallel module batches likewise
  remained failure-free before expiring between 40% and 47%; a definitive full
  run requires a less resource-constrained test environment.
- Frontend full suite: the fully parallel run completed with seven asynchronous
  loading-state timeouts across otherwise passing files. The implicated
  counselor, parent, school-admin and system-admin files pass in focused runs.
  A serial full-suite attempt, run alongside the backend batches, exceeded 300
  seconds. Treat the seven failures as unresolved suite-level
  concurrency/resource findings, not confirmed product defects.
- Initial frontend attempts inside the restricted sandbox were invalid because
  esbuild could not read `vite.config.ts`; the authorized production build
  confirmed that this was environmental rather than a source-code build error.

## Fix log

| Date | Finding | Change | Verification |
|---|---|---|---|
| 2026-07-31 | AUD-CONTENT-001 | Replaced the incorrect plural placement hostname with the verified Ministry selection service; separated selection, subject-catalogue and placement-outcome links; added the service-link check date. | 14 focused frontend tests passed; production build passed. |
| 2026-07-31 | AUD-CONTENT-006 | Replaced “Form 2–4 learners” with the application’s implemented Grade 9–10 audience. | Landing regression suite and production build passed. |
| 2026-07-31 | AUD-CODE-005 / AUD-CONTENT-008 | Added an explicit combination-selectability field, classified Core and Essential Mathematics as core, classified Physical Education as separately required, and preserved Mathematics in valid official combinations. | Migration consistency check passed; 72 focused backend tests and the production frontend build passed. |
| 2026-07-31 | AUD-CONTENT-007 | Replaced “county-verified registration” with “county-limited registration.” | TypeScript production build passed. |
| 2026-07-31 | AUD-CODE-001 / AUD-CODE-002 / AUD-CONTENT-004 | Added per-record verification status, source URL and checked date for schools, combinations and offerings; classified seeded pilot institutions and offerings as demonstration data; excluded non-verified availability from public responses and filters; changed learner-facing wording to “verified school offering.” | Migration consistency check passed; 89 focused backend tests, 42 focused frontend tests and the production frontend build passed. |
| 2026-07-31 | AUD-CONTENT-002 | Reframed the school-photo gallery as documentary illustration, linked its Wikimedia source/licence record and added explicit non-participation, non-endorsement and availability language. | Landing-section regression test and production frontend build passed. |
| 2026-07-31 | AUD-CODE-002 | Added a reproducible Ministry identity snapshot (1,253 schools), official offering snapshot (623 exact relationships), checksum validation, dry-run/apply importers, quarantine rules and administrator evidence visibility. | 26 focused data-pipeline tests, Django checks, migration check and local presentation import passed. |
| 2026-07-31 | AUD-CODE-003 | Removed `fit_score` and `fit_pct` from assessment, parent, counsellor and report-facing contracts while retaining internal ranking snapshots. | Five targeted backend contract tests and production frontend build passed. |
| 2026-07-31 | AUD-CODE-004 / AUD-CONTENT-003 | Centralized frontend rollout counties, identified the five counties as project scope, and replaced the unsupported placement-factor list with a Ministry confirmation instruction. | Targeted backend tests and production frontend build passed. |

## Review areas

- Data provenance and hardcoded education-domain records
- Official-flow parity
- Misleading or predictive behavior
- Authentication, authorization and session handling
- Input validation and error recovery
- Learner privacy and access controls
- Accessibility and responsive behavior
- Low-bandwidth and offline behavior
- SNE and language support
- Unit, integration and environment-specific test coverage

Earlier review notes, including `docs/sprint-8-review-issues.md`, are leads only.
Each finding must be reproduced against this baseline before it is accepted.
