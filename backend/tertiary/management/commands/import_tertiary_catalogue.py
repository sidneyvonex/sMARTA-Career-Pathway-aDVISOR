import csv
from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.db import transaction

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


def _require(row, field, row_number):
    value = (row.get(field) or '').strip()
    if not value:
        raise CommandError(f'Row {row_number}: {field} is required.')
    return value


def _validate_rows(path):
    try:
        handle = path.open(newline='', encoding='utf-8-sig')
    except OSError as exc:
        raise CommandError(f'Cannot read CSV: {exc}') from exc
    with handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise CommandError('CSV header does not match the documented schema exactly.')
        rows = []
        seen = set()
        for row_number, raw in enumerate(reader, start=2):
            row = {key: (value or '').strip() for key, value in raw.items()}
            record_type = _require(row, 'record_type', row_number)
            if record_type not in RECORD_TYPES:
                raise CommandError(f'Row {row_number}: unsupported record_type {record_type}.')
            for field in PROVENANCE_FIELDS:
                _require(row, field, row_number)
            identity = (row['source_scope'], row['external_key'])
            if identity in seen:
                raise CommandError(f'Row {row_number}: duplicate source_scope/external_key.')
            seen.add(identity)
            try:
                URLValidator()(row['source_url'])
                row['_effective_date'] = date.fromisoformat(row['effective_date'])
            except (ValidationError, ValueError) as exc:
                raise CommandError(f'Row {row_number}: invalid source_url or effective_date.') from exc
            if row['verification_status'] not in dict(Institution.VERIFICATION_CHOICES):
                raise CommandError(f'Row {row_number}: invalid verification_status.')
            if record_type == 'institution':
                _require(row, 'name', row_number)
                if row['institution_type'] not in dict(Institution.TYPE_CHOICES):
                    raise CommandError(f'Row {row_number}: invalid institution_type.')
                if row['website_url']:
                    try:
                        URLValidator()(row['website_url'])
                    except ValidationError as exc:
                        raise CommandError(f'Row {row_number}: invalid website_url.') from exc
            elif record_type == 'programme':
                _require(row, 'parent_external_key', row_number)
                _require(row, 'name', row_number)
            elif record_type == 'programme_subject_reference':
                _require(row, 'parent_external_key', row_number)
                _require(row, 'subject_code', row_number)
                _require(row, 'subject_name', row_number)
                if row['mapping_kind'] not in dict(ProgrammeSubjectReference.KIND_CHOICES):
                    raise CommandError(f'Row {row_number}: invalid mapping_kind.')
            else:
                _require(row, 'parent_external_key', row_number)
                _require(row, 'requirement_summary', row_number)
                if row['education_framework'] != 'KCSE' or row['verification_status'] != 'historical':
                    raise CommandError(
                        f'Row {row_number}: historical admission references require '
                        'education_framework KCSE and verification_status historical.'
                    )
            rows.append(row)
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
            (row['source_scope'], row['external_key'])
            for row in by_type['institution']
        }
        imported_programmes = {
            (row['source_scope'], row['external_key'])
            for row in by_type['programme']
        }
        for row in by_type['programme']:
            parent = (row['source_scope'], row['parent_external_key'])
            if parent not in imported_institutions and not Institution.objects.filter(
                source_scope=parent[0], external_key=parent[1]
            ).exists():
                raise CommandError(f"Programme {row['external_key']}: parent institution not found.")
        for record_type in ('programme_subject_reference', 'historical_admission_reference'):
            for row in by_type[record_type]:
                parent = (row['source_scope'], row['parent_external_key'])
                if parent not in imported_programmes and not Programme.objects.filter(
                    source_scope=parent[0], external_key=parent[1]
                ).exists():
                    raise CommandError(f"Reference {row['external_key']}: parent programme not found.")

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
        label = 'Validated' if options['dry_run'] else 'Imported'
        self.stdout.write(self.style.SUCCESS(f'{label} {len(rows)} catalogue rows.'))
