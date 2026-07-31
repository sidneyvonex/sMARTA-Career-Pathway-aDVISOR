# Content Audit

**Baseline:** `origin/main` at `65fd088f9af97fddaea208796aca265ae9310c70`
**Status:** Initial claim inventory complete; one placement-policy claim remains unverified

| ID | Page or file | Audience | Claim | Source | Status | Risk | Required fix |
|---|---|---|---|---|---|---|---|
| AUD-CONTENT-001 | `frontend/src/components/landing/LandingNotice.tsx:74` | Learner and parent | Official Senior School choices are submitted at `placements.education.go.ke`, presented through an “Apply officially” action. | Current Ministry selection and placement platforms checked 2026-07-31. | `CONTRADICTED` | Critical: the app sends a learner to the wrong hostname. The official selection service is `selection.education.go.ke`; placement outcomes use `placement.education.go.ke`. | Replace the plural hostname everywhere, distinguish selection from placement outcomes and add a checked date near the external action. |
| AUD-CONTENT-002 | `frontend/src/components/landing/LandingCommunity.tsx:60` | All public visitors | The page claimed every pictured school was real and within the supported region, while presentation could imply participation or endorsement. | Wikimedia Commons credits exist in `frontend/public/img/CREDITS.md`; no product-participation evidence is stored. | `FIXED` | The former wording made an institutional claim it could not trace and could imply school participation or endorsement. | Reframed the images as documentary illustration, linked the source/licence record and added explicit non-participation, non-endorsement and availability disclaimers. |
| AUD-CONTENT-003 | `frontend/src/components/landing/LandingNotice.tsx:81` | Learner and parent | Final placement weighs choices, KJSEA performance, equity and school capacity. | No citation stored with the claim. | `UNVERIFIED` | Placement criteria can change by cohort; incomplete wording may influence real choices. | Verify against the current MoE placement communication and date-stamp the explanation. |
| AUD-CONTENT-004 | `backend/guidance/migrations/0002_seed_pilot_catalogue.py:10` | All catalogue consumers | The curated catalogue was verified against the Ministry’s subject-combination list. | The ten seeded codes were sampled against the current official selection-host catalogue on 2026-07-31; per-combination source and checked date are now stored. | `FIXED` | Without per-record evidence, a database description asserted verification more strongly than the available audit trail supported. | Implemented; retain source metadata whenever combinations are imported or changed. |
| AUD-CONTENT-005 | Public and authenticated guidance pages | Learner, parent and counsellor | Smarta Shauri is advisory and does not predict success, perform placement or submit official choices. | Internal product positioning; consistently visible in reviewed pages. | `VERIFIED` | Positive safeguard; regression could reintroduce misleading claims. | Retain and cover the disclaimer in content tests. |
| AUD-CONTENT-006 | `frontend/src/components/landing/LandingHero.tsx:9` | Learner and parent | The pilot is for “Form 2–4 learners.” | The official selection system describes Grade 9 learners transitioning to Grade 10; the application model supports Grades 9 and 10. | `CONTRADICTED` | The terminology targets the wrong cohort and mixes the former form system with CBE grade terminology. | Replace with the verified pilot audience after the five-county scope is confirmed; at minimum use “Grade 9–10 learners” for the implemented product. |
| AUD-CONTENT-007 | `frontend/src/pages/AboutPage.tsx:9` | Public visitors and schools | Registration is “county-verified.” | Current code accepts a county choice but contains no county-verification process. | `CONTRADICTED` | Users may believe their residence or eligibility was independently checked. | Use “county-limited” or explain the actual validation performed. |
| AUD-CONTENT-008 | `backend/students/migrations/0005_correct_grade10_catalogue.py:9` | Learners, parents, counsellors and reports | Physical Education was core, while Core/Essential Mathematics were elective. | KICD Grade 10 addendum, December 2025, checked 2026-07-31. | `FIXED` | Incorrect curriculum classification could distort guidance and subject summaries. | Implemented through a new curriculum-role/combination-selectability distinction and corrective data migration. |

## Implemented corrections

- **AUD-CONTENT-001:** corrected public selection links to
  `https://selection.education.go.ke`, added the verified official catalogue
  and separated the placement-outcome action.
- **AUD-CONTENT-006:** changed the public audience label from Forms 2–4 to
  Grades 9–10.
- **AUD-CONTENT-007:** changed “county-verified” to “county-limited” because the
  application does not independently verify residence.
- **AUD-CONTENT-008:** classified Core and Essential Mathematics as core,
  Physical Education as separately required, and preserved Mathematics as
  selectable within official subject combinations.
- **AUD-CONTENT-004:** attached the current official catalogue URL, verification
  state and check date to each seeded combination. Demonstration schools and
  offerings are now excluded from public availability.
- **AUD-CONTENT-002:** removed the unsupported “every school is real and
  in-region” claim, linked the image sources and licences, and clarified that
  appearance does not indicate participation, endorsement or availability.

These corrections were verified by 42 focused frontend tests, 89 focused
backend tests and a successful production build on 2026-07-31.

## Priority checks

1. Compulsory-subject lists.
2. Pathway-to-career mappings.
3. Selection and placement procedures.
4. School cluster explanations.
5. Percentages, quotas, scores and prediction language.
6. Claims that the application performs or guarantees official placement.
