# Official Portal Analysis

**Status:** Public, unauthenticated inventory started

**Audit opened:** 2026-07-31

**Audience:** Learners, parents/guardians and counsellors/teachers

No portal behavior is recorded as fact until it has been observed in an official
public flow or supported by current official documentation. Real learner
credentials and personal information must not be captured in audit evidence.

## Portal inventory

| Portal or service | Purpose | Access observed | Last checked | Evidence |
|---|---|---|---|---|
| `selection.education.go.ke` | Grade 10 pathway, subject-combination and senior-school selection | Public About, pathways and school-search content indexed; authenticated submission not yet inspected | 2026-07-31 | https://selection.education.go.ke/about |
| `placement.education.go.ke` | Placement management and learner placement outcomes | Public landing page and outcome form indexed | 2026-07-31 | https://placement.education.go.ke/ |
| `placement.education.go.ke/my-placements` | Check Grade 10 placement outcome | Form requests assessment number, junior-school KNEC code and privacy declaration | 2026-07-31 | https://placement.education.go.ke/my-placements |
| `selection.education.go.ke/schools` | Browse official senior schools | Public table exposes institution name, sex, KNEC code, cluster, accommodation and information; region/county/sub-county filters observed | 2026-07-31 | https://selection.education.go.ke/schools |

## Flow mapping

| Official step | Official fields and validation | Application equivalent | Gap or deviation | Severity | Evidence |
|---|---|---|---|---|---|
| Learn about selection | Official About page explains that selection records choices but does not perform placement | Public About, Pathways and How It Works pages | Broad purpose matches, but the app currently links to an incorrect plural hostname | Critical | Official About page and `frontend/src/components/landing/LandingNotice.tsx:74` |
| Browse subject combinations | Official pathway pages show combination, pathway, track, code and schools offering it | Combination explorer | The app uses a small sampled official combination list but pairs it with synthetic schools and offerings | High | Official catalogue PDF; `backend/guidance/migrations/0002_seed_pilot_catalogue.py` |
| Browse schools | Region, county and sub-county filters; school table includes KNEC code, cluster, sex and accommodation | Pilot-school filtering by county and school | App lacks official school codes, clusters, gender, accommodation and per-record verification | High | Official schools page; guidance serializers and explorer |
| Check placement outcome | Assessment number, junior-school KNEC code and privacy declaration | Public page links to a KJSEA results service, not the verified Grade 10 placement outcome form | The selection, assessment-results and placement-outcome services are not clearly distinguished | High | Official placement outcome form; `frontend/src/components/landing/LandingNotice.tsx` |

## Filters and accessibility

The audit will record county, cluster, pathway, accommodation, gender and SNE
filters only where they are directly observed or documented by an official
source.

## Privacy constraints

- Do not publish assessment numbers, names or other learner identifiers.
- Use official demonstrations, public documentation or explicitly authorized
  test access.
- Redact personal information from screenshots before adding them as evidence.
