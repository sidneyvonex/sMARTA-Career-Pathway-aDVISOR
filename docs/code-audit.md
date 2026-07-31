# Code Audit

**Baseline:** `origin/main` at `65fd088f9af97fddaea208796aca265ae9310c70`
**Status:** Initial repository inventory complete; deeper flow and test review in progress

| ID | Severity | Area | Finding | Evidence | User impact | Recommendation | Verification |
|---|---|---|---|---|---|---|---|
| AUD-CODE-001 | High | Data integrity | A production data migration creates five synthetic schools with `PILOT-*` codes and assigns curated offerings. The public combination API serializes these schools and the learner explorer describes combinations as offered by pilot schools. The records are visibly named as Smarta Shauri pilot schools, but they have no machine-readable demonstration-data flag. | `backend/guidance/migrations/0002_seed_pilot_catalogue.py:130`; `backend/guidance/serializers.py:69`; `frontend/src/pages/CombinationExplorerPage.tsx:242` | A learner or parent can interpret demonstration offerings as verified real-school availability. | Add an explicit data classification such as `demonstration`/`verified`, prevent demonstration schools from appearing as authoritative, and require provenance before publishing real offerings. | Code path confirmed; policy impact awaits official-data review. |
| AUD-CODE-002 | High | Provenance | Provenance exists only at framework level. `School`, `SubjectCombination` and `SchoolOffering` do not store per-record source, checked date or verification status. | `backend/guidance/models.py:10`; `backend/guidance/models.py:75`; `backend/guidance/models.py:173`; `backend/accounts/models.py:47` | The application cannot prove which school offering was checked, when it was checked or whether it is official. | Introduce per-record provenance and verification state before importing authoritative school data. Keep unverified records hidden or clearly labelled. | Confirmed against current models. |
| AUD-CODE-003 | Medium | Guidance algorithm | The backend calculates, stores and exposes a numeric `fit_pct` for pathway alignment through assessment, counsellor, parent and report data contracts. Current reviewed UI generally replaces the number with qualitative wording, but the numeric field remains available for accidental reuse. | `backend/riasec/scoring.py:42`; `backend/riasec/serializers.py:24`; `backend/reports/views.py:228`; `frontend/src/api/parent.ts:36` | A percentage can be mistaken for eligibility, success probability or placement likelihood. | Rename or remove the public percentage contract, document the scale, and retain only rank/explanation unless a validated user need requires the number. | Storage and API exposure confirmed; remaining consumers still being audited. |
| AUD-CODE-004 | Medium | Pilot scope | The same five counties are hardcoded in backend model choices and repeated in several frontend forms and filters. The authoritative pilot-county list has not yet been verified. | `backend/accounts/models.py:5`; `frontend/src/pages/RegisterPage.tsx:7`; `frontend/src/pages/CombinationExplorerPage.tsx:12` | Registration and administration reject every county outside an unverified internal list, and future policy changes require coordinated code edits. | Verify the scope, then move it to versioned configuration/reference data with source metadata. | Hardcoding confirmed; county list remains `UNVERIFIED`. |
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
- Focused backend guidance/catalogue/model suite: **72 passed** on 2026-07-31.
- Focused frontend official-link regression suite: **14 passed** on 2026-07-31.
- Backend full suite: started successfully but exceeded the 60-second audit command
  window; split-suite results are pending.
- Frontend full suite: started successfully with React Router warnings and two
  jsdom navigation warnings, then exceeded the command window; split-suite
  results are pending.
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
