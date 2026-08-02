import csv
from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from tertiary.models import (
    HistoricalAdmissionReference,
    Institution,
    Programme,
    ProgrammeSubjectReference,
)


RECORD_TYPES = {
    'institution',
    'programme',
    'programme_subject_reference',
    'historical_admission_reference',
}
PROVENANCE_FIELDS = (
    'source_scope', 'external_key', 'source_url', 'education_framework',
    'admission_cycle', 'effective_date', 'verification_status',
)
EXPECTED_COLUMNS = (
    'record_type', 'source_scope', 'external_key', 'parent_external_key',
    'name', 'code', 'institution_type', 'county', 'website_url', 'description',
    'subject_code', 'subject_name', 'mapping_kind', 'requirement_summary',
    'source_url', 'education_framework', 'admission_cycle', 'effective_date',
    'verification_status',
)
MODEL_FIELDS = {
    'institution': {
        'source_scope': 'source_scope', 'external_key': 'external_key',
        'source_url': 'source_url', 'education_framework': 'education_framework',
        'admission_cycle': 'admission_cycle', 'effective_date': '_effective_date',
        'verification_status': 'verification_status', 'name': 'name',
        'institution_type': 'institution_type', 'county': 'county',
        'website_url': 'website_url',
    },
    'programme': {
        'source_scope': 'source_scope', 'external_key': 'external_key',
        'source_url': 'source_url', 'education_framework': 'education_framework',
        'admission_cycle': 'admission_cycle', 'effective_date': '_effective_date',
        'verification_status': 'verification_status', 'code': 'code', 'name': 'name',
        'description': 'description',
    },
    'programme_subject_reference': {
        'source_scope': 'source_scope', 'external_key': 'external_key',
        'source_url': 'source_url', 'education_framework': 'education_framework',
        'admission_cycle': 'admission_cycle', 'effective_date': '_effective_date',
        'verification_status': 'verification_status', 'subject_code': 'subject_code',
        'subject_name': 'subject_name', 'mapping_kind': 'mapping_kind',
        'notes': 'description',
    },
    'historical_admission_reference': {
        'source_scope': 'source_scope', 'external_key': 'external_key',
        'source_url': 'source_url', 'education_framework': 'education_framework',
        'admission_cycle': 'admission_cycle', 'effective_date': '_effective_date',
        'verification_status': 'verification_status',
        'requirement_summary': 'requirement_summary',
    },
}
MODEL_BY_TYPE = {
    'institution': Institution,
    'programme': Programme,
    'programme_subject_reference': ProgrammeSubjectReference,
    'historical_admission_reference': HistoricalAdmissionReference,
}


def _require(row, field, row_number):
    value = (row.get(field) or '').strip()
    if not value:
        raise CommandError(f'Row {row_number}: {field} is required.')
    return value


def _validate_model_fields(row, row_number):
    model = MODEL_BY_TYPE[row['record_type']]
    for model_field, row_field in MODEL_FIELDS[row['record_type']].items():
        try:
            model._meta.get_field(model_field).clean(row[row_field], None)
        except ValidationError as exc:
            message = '; '.join(exc.messages)
            raise CommandError(
                f'Row {row_number}: invalid {model_field}: {message}'
            ) from exc


def _validate_rows(path):
    try:
        handle = path.open(newline='', encoding='utf-8-sig')
    except OSError as exc:
        raise CommandError(f'Cannot read CSV: {exc}') from exc
    with handle:
        try:
            reader = csv.DictReader(
                handle, restkey='__overflow__', restval=None, strict=True
            )
            if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
                raise CommandError('CSV header does not match the documented schema exactly.')
            rows = []
            seen = set()
            for row_number, raw in enumerate(reader, start=2):
                if raw.get('__overflow__') is not None:
                    raise CommandError(f'Row {row_number}: too many columns.')
                missing_columns = [
                    field for field in EXPECTED_COLUMNS if raw.get(field) is None
                ]
                if missing_columns:
                    raise CommandError(
                        f'Row {row_number}: too few columns; missing '
                        f'{", ".join(missing_columns)}.'
                    )
                row = {key: raw[key].strip() for key in EXPECTED_COLUMNS}
                record_type = _require(row, 'record_type', row_number)
                if record_type not in RECORD_TYPES:
                    raise CommandError(f'Row {row_number}: unsupported record_type {record_type}.')
                for field in PROVENANCE_FIELDS:
                    _require(row, field, row_number)
                identity = (record_type, row['source_scope'], row['external_key'])
                if identity in seen:
                    raise CommandError(
                        f'Row {row_number}: duplicate record_type/source_scope/external_key.'
                    )
                seen.add(identity)
                try:
                    row['_effective_date'] = date.fromisoformat(row['effective_date'])
                except ValueError as exc:
                    raise CommandError(f'Row {row_number}: invalid effective_date.') from exc
                if record_type == 'institution':
                    _require(row, 'name', row_number)
                elif record_type == 'programme':
                    _require(row, 'parent_external_key', row_number)
                    _require(row, 'name', row_number)
                elif record_type == 'programme_subject_reference':
                    _require(row, 'parent_external_key', row_number)
                    _require(row, 'subject_code', row_number)
                    _require(row, 'subject_name', row_number)
                    if row['mapping_kind'] == 'historical_requirement' and (
                        row['education_framework'] != 'KCSE'
                        or row['verification_status'] != 'historical'
                    ):
                        raise CommandError(
                            f'Row {row_number}: historical requirements require '
                            'education_framework KCSE and verification_status historical.'
                        )
                else:
                    _require(row, 'parent_external_key', row_number)
                    _require(row, 'requirement_summary', row_number)
                    if row['education_framework'] != 'KCSE' or row['verification_status'] != 'historical':
                        raise CommandError(
                            f'Row {row_number}: historical admission references require '
                            'education_framework KCSE and verification_status historical.'
                        )
                _validate_model_fields(row, row_number)
                rows.append(row)
        except (csv.Error, UnicodeError) as exc:
            raise CommandError(f'Malformed CSV: {exc}') from exc
    if not rows:
        raise CommandError('CSV contains no catalogue rows.')
    return rows


def _provenance(row):
    return {
        'source_url': row['source_url'],
        'education_framework': row['education_framework'],
        'admission_cycle': row['admission_cycle'],
        'effective_date': row['_effective_date'],
        'verification_status': row['verification_status'],
    }


def _assert_parent_coherence(row, parent, label):
    errors = []
    for field in ('source_scope', 'education_framework', 'admission_cycle'):
        parent_value = parent[field] if isinstance(parent, dict) else getattr(parent, field)
        if row[field] != parent_value:
            errors.append(field)
    authority = {'unavailable': 0, 'historical': 1, 'verified': 2}
    parent_status = (
        parent['verification_status']
        if isinstance(parent, dict)
        else parent.verification_status
    )
    if authority[row['verification_status']] > authority[parent_status]:
        errors.append('verification_status')
    if errors:
        raise CommandError(
            f"{label} {row['external_key']}: parent contradicts "
            f"{', '.join(errors)}."
        )


class Command(BaseCommand):
    help = 'Import the documented, source-scoped tertiary catalogue CSV without network access.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        path = Path(options['csv_path'])
        rows = _validate_rows(path)
        by_type = {
            record_type: [row for row in rows if row['record_type'] == record_type]
            for record_type in RECORD_TYPES
        }
        imported_institutions = {
            (row['source_scope'], row['external_key']): row
            for row in by_type['institution']
        }
        imported_programmes = {
            (row['source_scope'], row['external_key']): row
            for row in by_type['programme']
        }
        for row in by_type['programme']:
            parent = (row['source_scope'], row['parent_external_key'])
            parent_record = imported_institutions.get(parent) or Institution.objects.filter(
                source_scope=parent[0], external_key=parent[1]
            ).first()
            if parent_record is None:
                raise CommandError(f"Programme {row['external_key']}: parent institution not found.")
            _assert_parent_coherence(row, parent_record, 'Programme')
        for record_type in ('programme_subject_reference', 'historical_admission_reference'):
            for row in by_type[record_type]:
                parent = (row['source_scope'], row['parent_external_key'])
                parent_record = imported_programmes.get(parent) or Programme.objects.filter(
                    source_scope=parent[0], external_key=parent[1]
                ).first()
                if parent_record is None:
                    raise CommandError(f"Reference {row['external_key']}: parent programme not found.")
                _assert_parent_coherence(row, parent_record, 'Reference')

        try:
            with transaction.atomic():
                for row in by_type['institution']:
                    Institution.objects.update_or_create(
                        source_scope=row['source_scope'], external_key=row['external_key'],
                        defaults={
                            'name': row['name'], 'institution_type': row['institution_type'],
                            'county': row['county'], 'website_url': row['website_url'],
                            **_provenance(row),
                        },
                    )
                for row in by_type['programme']:
                    institution = Institution.objects.get(
                        source_scope=row['source_scope'], external_key=row['parent_external_key']
                    )
                    Programme.objects.update_or_create(
                        source_scope=row['source_scope'], external_key=row['external_key'],
                        defaults={
                            'institution': institution, 'code': row['code'], 'name': row['name'],
                            'description': row['description'], **_provenance(row),
                        },
                    )
                for row in by_type['programme_subject_reference']:
                    programme = Programme.objects.get(
                        source_scope=row['source_scope'], external_key=row['parent_external_key']
                    )
                    ProgrammeSubjectReference.objects.update_or_create(
                        source_scope=row['source_scope'], external_key=row['external_key'],
                        defaults={
                            'programme': programme, 'subject_code': row['subject_code'],
                            'subject_name': row['subject_name'], 'mapping_kind': row['mapping_kind'],
                            'notes': row['description'], **_provenance(row),
                        },
                    )
                for row in by_type['historical_admission_reference']:
                    programme = Programme.objects.get(
                        source_scope=row['source_scope'], external_key=row['parent_external_key']
                    )
                    HistoricalAdmissionReference.objects.update_or_create(
                        source_scope=row['source_scope'], external_key=row['external_key'],
                        defaults={
                            'programme': programme,
                            'requirement_summary': row['requirement_summary'],
                            **_provenance(row),
                        },
                    )
                if options['dry_run']:
                    transaction.set_rollback(True)
        except (ValidationError, IntegrityError) as exc:
            raise CommandError(f'Catalogue rows failed validated persistence: {exc}') from exc
        label = 'Validated' if options['dry_run'] else 'Imported'
        self.stdout.write(self.style.SUCCESS(f'{label} {len(rows)} catalogue rows.'))
