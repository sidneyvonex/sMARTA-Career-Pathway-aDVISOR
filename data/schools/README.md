# Official School Data

`official-schools-2026-07-31.json` is a reproducible identity snapshot from the
Kenya Ministry of Education senior-school directory. It covers the project's
five-county rollout scope; this is an internal product scope, not a claim that
the Ministry operates an official five-county pilot.

Snapshot summary:

- source checked: 31 July 2026;
- 1,253 unique Ministry school records from 49 sub-county queries;
- Kiambu 334, Kirinyaga 158, Murang'a 341, Nyandarua 194, and Nyeri 226;
- SHA-256: `25b3fcd66bd898a2db7a2715bc15bb9983f84df8f2f90232503a59a5d0a521a6`.

`official-offerings-2026-07-31.json` separately records 623 verified
school/combination relationships for the 10 curated combinations. All 623
Ministry offering rows matched exactly to one identity; zero rows were
quarantined. It was produced from 50 combination/county queries and has
SHA-256 `25e316202d3c1ec060c13dc72d8310e91fbd5de0d39320a631b74b2e3681ffdc`.

The complete catalogue is now the primary dataset:

- `official-catalogue-2026-07-31.json`: 511 combinations across seven tracks
  and 35 subject labels; SHA-256
  `9ddac3cbac55461df90b108bc4601d570495b14768998569ddd2c671760017db`;
- `official-offerings-full-2026-07-31.json`: 10,263 exact offering
  relationships from 2,555 combination/county queries; SHA-256
  `06fffc6180ab758e39a5d24725996427750c916b270a8d4097fa6cce1e8fc971`;
- county offering counts: Kiambu 3,131, Murang'a 2,796, Nyeri 1,779,
  Kirinyaga 1,263 and Nyandarua 1,294;
- 1,225 of the 1,253 schools have at least one recorded offering, and 363 of
  the 511 official combinations have at least one offering in the rollout
  counties.

The earlier 10-combination offering snapshot is retained as audit history but
is superseded for application seeding by the complete snapshots.

The public directory provides a stable source UUID, name, gender, cluster and
institution type, but it does not provide the KNEC school code. The importer
therefore stores the UUID separately as `source_record_id` and leaves
`school_code` empty. A source UUID must never be presented as a KNEC code.

Fetch a new snapshot:

```powershell
python backend/manage.py fetch_official_schools `
  --output data/schools/official-schools-YYYY-MM-DD.json `
  --checked-at YYYY-MM-DD
```

Preview and then apply an import:

```powershell
python backend/manage.py import_official_schools `
  --source data/schools/official-schools-2026-07-31.json `
  --expected-sha256 25b3fcd66bd898a2db7a2715bc15bb9983f84df8f2f90232503a59a5d0a521a6

python backend/manage.py import_official_schools `
  --source data/schools/official-schools-2026-07-31.json `
  --expected-sha256 25b3fcd66bd898a2db7a2715bc15bb9983f84df8f2f90232503a59a5d0a521a6 `
  --apply
```

School identity verification does not verify pathways or subject offerings.
Those relationships require separate official evidence, a checked date and an
explicit verification status. Ambiguous or incomplete matches must be
quarantined rather than exposed as authoritative data.

Fetch, preview and apply offering evidence:

```powershell
python backend/manage.py fetch_official_offerings `
  --schools data/schools/official-schools-2026-07-31.json `
  --output data/schools/official-offerings-2026-07-31.json `
  --checked-at 2026-07-31

python backend/manage.py import_official_offerings `
  --source data/schools/official-offerings-2026-07-31.json `
  --expected-sha256 25e316202d3c1ec060c13dc72d8310e91fbd5de0d39320a631b74b2e3681ffdc

python backend/manage.py import_official_offerings `
  --source data/schools/official-offerings-2026-07-31.json `
  --expected-sha256 25e316202d3c1ec060c13dc72d8310e91fbd5de0d39320a631b74b2e3681ffdc `
  --apply
```

For the complete catalogue, fetch/import the catalogue before its offerings:

```powershell
python backend/manage.py fetch_official_catalogue `
  --output data/schools/official-catalogue-YYYY-MM-DD.json `
  --checked-at YYYY-MM-DD

python backend/manage.py import_official_catalogue `
  --source data/schools/official-catalogue-2026-07-31.json `
  --expected-sha256 9ddac3cbac55461df90b108bc4601d570495b14768998569ddd2c671760017db `
  --apply

python backend/manage.py fetch_official_offerings `
  --schools data/schools/official-schools-2026-07-31.json `
  --catalogue data/schools/official-catalogue-2026-07-31.json `
  --output data/schools/official-offerings-full-2026-07-31.json `
  --checked-at 2026-07-31 `
  --checkpoint-every 25 `
  --resume

python backend/manage.py import_official_offerings `
  --source data/schools/official-offerings-full-2026-07-31.json `
  --expected-sha256 06fffc6180ab758e39a5d24725996427750c916b270a8d4097fa6cce1e8fc971 `
  --apply
```
