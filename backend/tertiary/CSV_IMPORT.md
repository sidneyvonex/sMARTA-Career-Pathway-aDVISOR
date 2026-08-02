# Tertiary catalogue CSV

`python manage.py import_tertiary_catalogue PATH [--dry-run]` consumes a UTF-8
CSV locally. It performs no network requests, validates the complete file before
writing, and applies all rows atomically. `--dry-run` performs the same validation
and database resolution but rolls back all writes.

The header is fixed and ordered:

```text
record_type,source_scope,external_key,parent_external_key,name,code,institution_type,county,website_url,description,subject_code,subject_name,mapping_kind,requirement_summary,source_url,education_framework,admission_cycle,effective_date,verification_status
```

Every row requires `record_type`, `source_scope`, `external_key`, `source_url`,
`education_framework`, `admission_cycle`, ISO `effective_date`, and
`verification_status`. Parent keys resolve within the same `source_scope`.
Supported record types are `institution`, `programme`,
`programme_subject_reference`, and `historical_admission_reference`.
Subject mappings accept only `historical_requirement` or
`exploratory_alignment`. Re-importing the same `(source_scope, external_key)`
updates that source record rather than creating a duplicate.
