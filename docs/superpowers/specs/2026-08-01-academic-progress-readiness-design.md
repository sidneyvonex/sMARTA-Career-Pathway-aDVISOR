# Academic Progress and Education Goals Design Contract

**Date:** 2026-08-01
**Status:** Approved implementation contract
**Applies to:** Academic Progress and Readiness for Grades 10–12

This is the authoritative product and safety contract for Academic Progress and Education Goals. Every later API, UI, report, test, seed-data, and rollout decision in this scope must follow it. It supersedes an older pilot document where the two conflict.

## Product outcome and terminology

Smarta Shauri helps a learner and support network understand longitudinal academic evidence, receive an explainable support status, set an academic improvement target, and explore tertiary institutions or programmes. It is an advisory planning product: it does not perform official CBE placement, decide admission, predict admission, or replace professional counselling.

Use **CBE** for the wider Competency-Based Education system; use **CBC** only for the curriculum. Use **academic evidence**, **assessment framework**, **continuity code**, **academic progress**, and **academic readiness** as defined below. Academic readiness is a deterministic evidence status, never a prediction or score. Use **support**, **insufficient evidence**, **needs attention**, **strong**, and **on track** for its outcomes.

An **academic goal** is a learner improvement target for one continuity code. An **education goal** is an exploratory institution and/or programme choice. Keep the concepts, models, endpoints, UI flows, evidence, and calls to action separate. A **historical reference** is source-dated material from an earlier framework or cycle.

Never call a CBE level a KCSE grade, cluster point, KJSEA score, admission score, admission probability, eligibility result, placement result, or official recommendation. Do not present a learner as eligible, ineligible, likely to be admitted, or having an admission chance.

## Non-negotiable safety rules

1. Never convert CBE performance levels into KCSE grades, cluster points, KJSEA scores, admission probabilities, unofficial eligibility, or a composite readiness/admission score.
2. `EE1`–`BE2` ordinal ranks are visualization and directional-comparison aids only. Never render, store, or describe their aggregate as a percentage, average, points total, or admission score.
3. Every status and alert exposes the records used, deterministic rule code, plain-language explanation, and suggested action. The returned evidence snapshot must reproduce its result.
4. School-verified evidence cannot be silently edited or deleted. It retains the verifying school. Only that verifying school may remove verification, and only while its membership is active; removing verification does not erase history.
5. Learner-entered and school-verified evidence are visibly distinguished in every evidence display, explanation, report, and export.
6. Historical KUCCPS material is reference material only: it names its **KCSE** framework/cycle, source URL, effective date, and **historical-reference** status. It is never converted or compared with CBE evidence to calculate eligibility or placement.
7. The only placement evaluator returns `official_criteria_unavailable` with source/framework metadata and explanatory copy. No heuristic may fill the gap.
8. Authenticated API responses are never cached by the service worker.
9. Registration remains limited to Grades 9 and 10. Models support Grades 9–12; Grade 11 and 12 catalogues activate only from authoritative data.

## Grade 10–12 evidence lifecycle

Each record retains its assessment framework/version, continuity code, academic grade, academic year, term, level, source, and timestamps. Official numeric ranges and points remain nullable when unavailable; they are never invented.

The Senior School pilot framework uses these CBE levels and directional ranks:

| Level | Ordinal rank |
| --- | ---: |
| EE1 | 8 |
| EE2 | 7 |
| ME1 | 6 |
| ME2 | 5 |
| AE1 | 4 |
| AE2 | 3 |
| BE1 | 2 |
| BE2 | 1 |

These ranks are not marks, percentages, points, or cross-framework equivalences. They support only directional comparison and the rules below.

Evidence is grouped by `continuity_code`, not a temporary subject-enrolment ID. An enrolment can be archived, but its grade rows remain. Only one active enrolment exists for the same learner, continuity code, and academic grade. History requires an explicit history-inclusive response.

Within one continuity code, order records by academic grade, academic year, term, then creation timestamp as the deterministic final tie breaker. Compare a record only with its immediately preceding available record. A decline has a lower ordinal rank; an improvement has a higher ordinal rank.

Learners can edit/delete only their unverified evidence on active enrolments. Verification stores the verifying school and time. Verified records are locked against learner mutation and mutation by another school. A school transfer ends the old membership but preserves historical evidence and verifying-school provenance. Grade mutations on archived enrolments are rejected with the standard error envelope and a specific, non-sensitive reason; the UI shows that reason and a toast.

## Deterministic progress outcomes and exact alert precedence

Derive one outcome per continuity code from the ordered evidence above. Evaluate these rules in this exact order and stop at the first match; a later rule never overrides an earlier match.

| Order | Match | Outcome | Stable rule code |
| ---: | --- | --- | --- |
| 1 | No evidence exists. | Insufficient evidence | `missing_evidence` |
| 2 | Latest is `BE1` or `BE2`. | Support | `latest_be_support` |
| 3 | Exactly one record exists and it is not `BE1` or `BE2`. | Insufficient evidence | `one_non_be_insufficient` |
| 4 | At least two records exist and the two latest are each `AE1`, `AE2`, `BE1`, or `BE2`. | Support | `two_ae_be_support` |
| 5 | Latest is `AE1` or `AE2`, or the two latest directional comparisons are declines. | Needs attention | `latest_ae_or_two_declines_attention` |
| 6 | Latest is `EE1` or `EE2`, or the latest comparison improves and latest is at least `ME2` (`ME2`, `ME1`, `EE2`, `EE1`). | Strong | `latest_ee_or_improving_to_me2_strong` |
| 7 | Any remaining evidence state. | On track | `otherwise_me_on_track` |

“Two declines” means two consecutive declines across the three latest available records. “Latest” is the final record after the mandated sort, not the most recently edited record. With no preceding record there is no improvement or decline. Return the winning rule's records, label, code, suggested action, evidence confidence, and advisory disclaimer.

Derive overall severity without scoring: `support` precedes `needs attention`, then `insufficient evidence`, then `on track`, then `strong`. The response names the subject outcomes that produced the overall result.

## Education-goal separation

`AcademicGoal` belongs to a continuity code and records current/target level, target period/grade, action plan, status, creator, and timestamps. One active goal per continuity code is permitted. Later evidence can make a target ready, but only the learner's explicit confirmation marks it achieved.

`LearnerEducationGoal` is an independent exploration choice for an institution and optionally a programme. Institution-only goals are valid. A learner may save one primary goal and up to two alternatives. Programme and subject references help exploration only; they do not produce eligibility or change an academic goal.

Academic goals are under `/api/v1/students/academic-goals/`; education goals are under `/api/v1/students/education-goals/`. The UI keeps their creation, status, evidence, and actions distinct even where it offers navigation cross-links.

## Role and object permissions

| Role | Permitted | Prohibited |
| --- | --- | --- |
| Learner | Manage own unverified active evidence, academic goals, education goals; read full own progress/history. | Mutating verified evidence, viewing another learner, treating exploration as eligibility. |
| Approved parent | Read-only learner-approved progress and goals. | Private/safeguarding notes, unapproved access, all evidence/goal mutation. |
| Assigned counsellor | Read assigned learner's evidence, explanations, and goals; create interventions in the intervention domain. | Mutating evidence or either goal type; access outside active assignment. |
| Active verifying school administrator | Verify active-member evidence; remove own school's verification while membership is active; read needed provenance/membership. | Mutating another school's verification; erasing transfer history. |
| System administrator | Manage framework and tertiary-source metadata; inspect authorized audit/provenance metadata. | Inventing ranges, authority, or eligibility outcomes. |

All endpoints use `{ data, error, message }`, cookie JWT authentication, existing permission classes, and object-level checks. Unauthorized and forbidden responses disclose no private evidence.

## Error, accessibility, and interaction contract

Required states are explicit and safe:

- No evidence uses `missing_evidence`, explains that no status is derivable, and offers the permitted evidence action.
- A single non-BE record uses `one_non_be_insufficient` and never implies a trend.
- Archived subjects reject grade mutation, preserve history, and offer no edit control. Verified records reject unauthorized mutation without exposing another learner's or school's private information.
- Pending/transfer membership displays its state, preserves provenance, and removes former-school verification actions once membership is inactive.
- Missing authoritative catalogue/criteria renders `official_criteria_unavailable` plus source/framework metadata and advisory copy; it never substitutes a heuristic.
- Loading provides clear feedback; recoverable failures provide retry. Failed user actions show a toast. Network, 403, 404, and 500 use respectively: `Connection error. Please check your internet.`, `You don't have permission to do that.`, `That item no longer exists.`, and `Server error. Please try again in a moment.` Raw API error objects are not user-facing feedback.

Use existing primitives and CSS variables. Every input has an associated label; controls are keyboard-operable with visible focus and at least `44px` touch targets. Trends/statuses have text equivalents independent of colour or chart shape. Provide reduced-motion behavior and verify responsive layouts at 360px, tablet, and desktop. Async buttons disable while submitting; every successful or failed action uses the standard success/loading/error toast.

## Test acceptance

Acceptance requires passing coverage for:

1. Framework uniqueness/status, ordered definitions, nullable ranges/points, raw-score validation, Grade 9–12 support, and immutable verifying-school provenance.
2. Continuity, archived enrolment, active-only listing, explicit history, duplicate-active constraints, and retained grade rows.
3. Transfer authorization/lifecycle, preserved evidence, verification locks, notifications, and audit events.
4. Every exact rule/precedence branch, chronology, confidence, evidence snapshot, overall severity, and no-percentage contract.
5. Academic-goal ownership, one-active constraint, target validation, lifecycle, learner confirmation, and counsellor read-only access.
6. Catalogue provenance, institution-only/programme goals, primary/alternative limits, validated idempotent import/rollback, and no eligibility/probability fields.
7. Role/object authorization, response envelope, an MSW handler for every new frontend endpoint, loading/error/retry/toasts, keyboard labels, reduced motion, and responsive behavior.
8. Authenticated service-worker-cache regression and retained mandatory labels and metadata on historical KCSE references.

Use the project's backend/frontend test stacks, existing API client, response, authentication, permission, and MSW conventions.

## Rollout and authoritative-source policy

Release additive backend contracts first and preserve existing API routes and envelopes while consumers migrate. Enable the unified `/grades` experience with `academic_progress_v1`; retain legacy grade history as the fallback for one release. The flag-off state must neither expose partial progress contracts nor remove existing history.

Roll out framework/provenance; continuity/membership safety; deterministic progress; academic goals; sourced tertiary exploration and unavailable evaluator; flagged learner UI; supporting roles/reports; then full verification. Every stage preserves evidence history and permission boundaries.

An authoritative source is an official, source-dated record suitable for its framework, catalogue, or criterion. Store source URL, effective date, framework/cycle, status, and import provenance with every framework and tertiary catalogue record. Use validated CSV imports with explicit metadata; do not runtime-scrape.

Only authoritative data activates Grade 11 or Grade 12 catalogues or may be described as current. Missing, expired, conflicting, or historical material is unavailable or clearly labelled historical reference, never silently upgraded or used for placement evaluation. KUCCPS remains historical unless its stored metadata establishes current framework/cycle; every display/export retains its KCSE framework/cycle, source URL, effective date, and historical-reference status. CBE evidence and historical KCSE records remain separate and cannot be transformed into one another.
