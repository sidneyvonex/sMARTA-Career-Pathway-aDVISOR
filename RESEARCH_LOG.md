# Research Log

All education-domain findings must include a source, tier, date checked and
confidence. A claim is not verified merely because it appears in an existing
project document.

| Date checked | Question | Finding | Source | Tier | Status | Confidence |
|---|---|---|---|---|---|---|
| 2026-07-31 | Which five counties define the project rollout? | Existing project documents name Kiambu, Murang'a, Nyeri, Kirinyaga and Nyandarua. This is an internal product boundary; no claim is made that it is a Ministry-designated pilot. | Internal project specification dated 2026-07-30 | Internal reference | `VERIFIED` as product scope | High |
| 2026-07-31 | What code version is the audit based on? | The audit branch is based on the latest `origin/main` merge commit, `65fd088f9af97fddaea208796aca265ae9310c70`, which includes PR #64 from `redesign/dashboard-internal`. | Local Git repository | Repository evidence | `VERIFIED` | High |
| 2026-07-31 | Where are learners expected to submit Grade 10 pathway, subject-combination and school choices? | The Ministry’s current Grade 10 Selection System is `https://selection.education.go.ke`. Its About page says it records and submits learner choices but does not perform placement. | https://selection.education.go.ke/about | Tier 1 — Ministry of Education | `VERIFIED` | High |
| 2026-07-31 | Where are Grade 10 placement outcomes checked? | The Ministry’s current placement platform is `https://placement.education.go.ke`; its outcome form requests the assessment number and junior-school KNEC code. | https://placement.education.go.ke/ and https://placement.education.go.ke/my-placements | Tier 1 — Ministry of Education | `VERIFIED` | High |
| 2026-07-31 | Is `placements.education.go.ke` the current official choice-submission service? | No current official source found uses the plural-host address. Current Ministry services use `selection.education.go.ke` for choice submission and `placement.education.go.ke` for outcomes. | Ministry selection and placement platforms above | Tier 1 — Ministry of Education | `CONTRADICTED` | High |
| 2026-07-31 | What are the current Grade 10 core learning areas? | KICD’s December 2025 Grade 10 addendum states that learners take four core learning areas: English, Kiswahili/KSL, Core or Essential Mathematics, and Community Service Learning. Physical Education is scheduled separately. | https://kicd.ac.ke/wp-content/uploads/2025/12/DOC-20251216-WA0023.pdf | Tier 1 — KICD | `VERIFIED` | High |
| 2026-07-31 | Is the project’s curated subject-combination source represented on the current official selection host? | The same numeric catalogue path is indexed on `selection.education.go.ke`, and sampled seeded codes including ST1042, ST2007, ST2067, ST3074, SS1006, SS2019, SS2033, AS1021, AS1049 and AS2009 appear in that official catalogue. | https://selection.education.go.ke/uploads/1750333580754-subject-combinations-1750333524964.pdf | Tier 1 — Ministry selection system | `VERIFIED` for sampled combinations | High |

| 2026-07-31 | Which official schools are present in the five-county rollout scope? | The Ministry public directory returned 1,253 unique source records from 49 uppercase sub-county queries: Kiambu 334, Murang'a 341, Nyeri 226, Kirinyaga 158 and Nyandarua 194. The endpoint exposes a Ministry UUID but not a KNEC school code. | https://selection.education.go.ke/schools and its public `school-search` endpoint | Tier 1 — Ministry selection system | `VERIFIED` identity snapshot | High |
| 2026-07-31 | Which rollout schools offer the 10 curated combinations? | Fifty official combination/county queries returned 623 school/combination rows. Every row matched exactly to one Ministry identity; zero were ambiguous or unmatched. | Ministry public `subject-combinations-by-track` and `schools-by-combination` endpoints under https://selection.education.go.ke | Tier 1 — Ministry selection system | `VERIFIED` offering snapshot | High |
| 2026-07-31 | Can the complete catalogue be reconciled within the five rollout counties? | All 511 unique combinations across seven tracks were reconciled to 35 local Grade 10 subjects. A checkpointed run of 2,555 combination/county queries produced 10,263 exact offering relationships, including 2,796 for Murang'a; zero rows were ambiguous or unmatched. | Ministry public `subject-combinations-by-track` and `schools-by-combination` endpoints under https://selection.education.go.ke | Tier 1 — Ministry selection system | `VERIFIED` full catalogue and offering snapshots | High |

## Status definitions

- `VERIFIED`: supported by the required authoritative evidence.
- `UNVERIFIED`: not yet checked against adequate evidence.
- `OUTDATED`: reliable for an earlier period but not current.
- `UNSUPPORTED`: no adequate evidence was found.
- `CONTRADICTED`: reliable evidence conflicts with the claim.

## Open verification queue

1. Current school-selection quantities and submission rules.
2. Current KJSEA result-checking and SMS instructions.
3. KNEC codes and SNE provisions not exposed by the public school directory.
