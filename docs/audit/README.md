# Senior School Guidance Audit

## Baseline

- Audit branch: `codex/senior-school-guidance-audit`
- Code baseline: latest `origin/main`
- Baseline commit: `65fd088f9af97fddaea208796aca265ae9310c70`
- Audit opened: 2026-07-31
- Intended audiences: learner, parent/guardian and counsellor/teacher

The audit assesses the code and content found on `main`. Documents written during
earlier pilot or redesign work are useful as intended-product references, but are
not evidence that a feature exists or that a policy claim is correct.

## Evidence rules

1. Code claims require a file reference and, where appropriate, a reproducible
   test or observed behavior.
2. Education-policy claims require a source URL, source tier and date checked.
3. School codes, clusters, pathways and subject combinations must never be
   inferred or filled in.
4. Conflicting sources are recorded rather than silently reconciled.
5. Unverified records are not presented as authoritative.

## Audit outputs

- `RESEARCH_LOG.md`
- `docs/official-portal-analysis.md`
- `docs/content-audit.md`
- `docs/code-audit.md`
- `data/schools/`
- Persona-specific FAQs, added only after the underlying facts are verified

## Branch boundary

PR #64 merged `redesign/dashboard-internal` into `origin/main` at the baseline
commit, so that implementation and its documentation are in audit scope. The
documents are marked as audit inputs because intended behavior is not proof of
correct implementation. Local mockups, screenshots and generated PDF output
remain local-only unless explicitly approved as deliverables.
