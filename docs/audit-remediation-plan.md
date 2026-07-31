# Audit Remediation and Rollout Plan

## Current completion state

| Workstream | Status | Evidence |
|---|---|---|
| Official school identities | Complete | 1,253 unique Ministry records across 49 sub-county queries; checksum-pinned snapshot. |
| Official combination catalogue | Complete | All 511 Ministry combinations across seven tracks and 35 subject labels imported. |
| Verified school offerings | Complete for five-county scope | 10,263 exact school/combination relationships; zero quarantined rows. |
| Local database seed | Complete | Presentation SQLite migrated; 1,253 schools, 511 combinations and 10,263 offerings imported. |
| Production database seed | Deployment pending | Run the same checksum-pinned commands after production database credentials and a backup are available. |
| Synthetic-data protection | Complete | Demonstration records are labelled and excluded from authoritative public availability. |
| Provenance and freshness visibility | Complete baseline | Source status and checked date are visible in system administration. |
| Numeric fit exposure | Complete | Public and role-facing contracts expose rank and explanation, not percentages or raw fit scores. |
| Placement wording | Complete | Unsupported factor claims removed; official confirmation required. |
| County-scope clarity | Complete baseline | Five counties are described as project rollout scope and frontend options are centralized. |
| Full-suite performance | Open, non-functional | Focused suites and production build pass; the full backend suite remains too slow in this workstation environment. |

## Production execution

1. Back up the target database and record the application release SHA.
2. Deploy the branch migrations and run `python backend/manage.py migrate --noinput`.
3. Run both import commands without `--apply`; require the documented record counts and checksums.
4. Apply the school identity import, then the offering import.
5. Verify database totals, five-county counts, 511 combinations, 10,263 verified offering pairs and zero duplicate source IDs.
6. Smoke-test registration, catalogue filters, school availability, learner plans and the system-admin evidence column.
7. Retain the JSON snapshots with the release and schedule a periodic re-fetch. Any changed, missing, ambiguous or new row stays quarantined until reviewed.

## Commands

The exact fetch, checksum, preview and apply commands are maintained in
`data/schools/README.md`. Import is intentionally dry-run-first and atomic.

## Definition of done

- No Ministry source UUID is shown or stored as a KNEC code.
- Only verified identities and verified offerings appear as authoritative availability.
- Every published offering has a source and checked date.
- Demonstration, unmatched and ambiguous data remain visibly non-authoritative.
- Guidance uses rank and explanation, never a success or placement percentage.
- The five counties are presented as current product scope, not Ministry policy.
