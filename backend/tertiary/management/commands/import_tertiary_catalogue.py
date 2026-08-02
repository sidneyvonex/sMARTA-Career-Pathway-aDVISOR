import csv
from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.db.models import Q

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
                row['_row_number'] = row_number
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


def _row_identity(row):
    return row['source_scope'], row['external_key']


def _lock_identities(model, identities):
    if not identities:
        return {}
    records = model.objects.select_for_update().filter(
        source_scope__in={scope for scope, _key in identities},
        external_key__in={key for _scope, key in identities},
    ).order_by('pk')
    return {
        (record.source_scope, record.external_key): record
        for record in records
        if (record.source_scope, record.external_key) in identities
    }


def _lock_catalogue_state(by_type):
    institution_targets = {
        _row_identity(row) for row in by_type['institution']
    }
    institution_parents = {
        (row['source_scope'], row['parent_external_key'])
        for row in by_type['programme']
    }
    institutions = _lock_identities(
        Institution, institution_targets | institution_parents
    )

    programme_targets = {
        _row_identity(row) for row in by_type['programme']
    }
    programme_parents = {
        (row['source_scope'], row['parent_external_key'])
        for record_type in (
            'programme_subject_reference', 'historical_admission_reference',
        )
        for row in by_type[record_type]
    }
    programmes = _lock_identities(
        Programme, programme_targets | programme_parents
    )
    updated_institution_ids = [
        institutions[identity].pk
        for identity in institution_targets
        if identity in institutions
    ]
    for programme in Programme.objects.select_for_update().filter(
        institution_id__in=updated_institution_ids
    ).order_by('pk'):
        programmes[(programme.source_scope, programme.external_key)] = programme

    updated_programme_ids = [
        programmes[identity].pk
        for identity in programme_targets
        if identity in programmes
    ]
    subject_targets = {
        _row_identity(row)
        for row in by_type['programme_subject_reference']
    }
    subjects = _lock_identities(ProgrammeSubjectReference, subject_targets)
    for reference in ProgrammeSubjectReference.objects.select_for_update().filter(
        programme_id__in=updated_programme_ids
    ).order_by('pk'):
        subjects[(reference.source_scope, reference.external_key)] = reference

    historical_targets = {
        _row_identity(row)
        for row in by_type['historical_admission_reference']
    }
    historical = _lock_identities(
        HistoricalAdmissionReference, historical_targets
    )
    for reference in HistoricalAdmissionReference.objects.select_for_update().filter(
        programme_id__in=updated_programme_ids
    ).order_by('pk'):
        historical[(reference.source_scope, reference.external_key)] = reference

    goal_filter = Q()
    if updated_institution_ids:
        goal_filter |= Q(institution_id__in=updated_institution_ids)
    if updated_programme_ids:
        goal_filter |= Q(programme_id__in=updated_programme_ids)
    if goal_filter:
        list(
            Institution._meta.apps.get_model(
                'tertiary', 'LearnerEducationGoal'
            ).objects.select_for_update().filter(goal_filter).order_by('pk')
        )
    return institutions, programmes, subjects, historical


def _assign(instance, values):
    for field, value in values.items():
        setattr(instance, field, value)


def _validate_instance(instance, row, *, exclude=()):
    try:
        instance.full_clean(
            exclude=set(exclude), validate_unique=False,
            validate_constraints=False,
        )
    except ValidationError as exc:
        raise CommandError(
            f"Row {row['_row_number']}: {instance._meta.verbose_name} "
            f'failed semantic validation: {exc}'
        ) from exc


def _prepare_catalogue(by_type):
    locked = _lock_catalogue_state(by_type)
    locked_institutions, locked_programmes, locked_subjects, locked_historical = locked
    prospective_institutions = {}
    prepared_institutions = []
    for row in by_type['institution']:
        identity = _row_identity(row)
        instance = locked_institutions.get(identity) or Institution(
            source_scope=identity[0], external_key=identity[1]
        )
        _assign(instance, {
            'name': row['name'], 'institution_type': row['institution_type'],
            'county': row['county'], 'website_url': row['website_url'],
            **_provenance(row),
        })
        _validate_instance(instance, row)
        prospective_institutions[identity] = instance
        prepared_institutions.append((row, instance))

    prospective_programmes = {}
    prepared_programmes = []
    for row in by_type['programme']:
        identity = _row_identity(row)
        parent_identity = (row['source_scope'], row['parent_external_key'])
        parent = prospective_institutions.get(parent_identity) or locked_institutions.get(
            parent_identity
        )
        if parent is None:
            raise CommandError(
                f"Programme {row['external_key']}: parent institution not found."
            )
        _assert_parent_coherence(row, parent, 'Programme')
        instance = locked_programmes.get(identity) or Programme(
            source_scope=identity[0], external_key=identity[1]
        )
        _assign(instance, {
            'institution': parent, 'code': row['code'], 'name': row['name'],
            'description': row['description'], **_provenance(row),
        })
        _validate_instance(instance, row, exclude={'institution'})
        prospective_programmes[identity] = instance
        prepared_programmes.append((row, instance, parent))

    prepared_subjects = []
    for row in by_type['programme_subject_reference']:
        identity = _row_identity(row)
        parent_identity = (row['source_scope'], row['parent_external_key'])
        parent = prospective_programmes.get(parent_identity) or locked_programmes.get(
            parent_identity
        )
        if parent is None:
            raise CommandError(
                f"Reference {row['external_key']}: parent programme not found."
            )
        _assert_parent_coherence(row, parent, 'Reference')
        instance = locked_subjects.get(identity) or ProgrammeSubjectReference(
            source_scope=identity[0], external_key=identity[1]
        )
        _assign(instance, {
            'programme': parent, 'subject_code': row['subject_code'],
            'subject_name': row['subject_name'], 'mapping_kind': row['mapping_kind'],
            'notes': row['description'], **_provenance(row),
        })
        _validate_instance(instance, row, exclude={'programme'})
        prepared_subjects.append((row, instance, parent))

    prepared_historical = []
    for row in by_type['historical_admission_reference']:
        identity = _row_identity(row)
        parent_identity = (row['source_scope'], row['parent_external_key'])
        parent = prospective_programmes.get(parent_identity) or locked_programmes.get(
            parent_identity
        )
        if parent is None:
            raise CommandError(
                f"Reference {row['external_key']}: parent programme not found."
            )
        _assert_parent_coherence(row, parent, 'Reference')
        instance = locked_historical.get(identity) or HistoricalAdmissionReference(
            source_scope=identity[0], external_key=identity[1]
        )
        _assign(instance, {
            'programme': parent,
            'requirement_summary': row['requirement_summary'],
            **_provenance(row),
        })
        _validate_instance(instance, row, exclude={'programme'})
        prepared_historical.append((row, instance, parent))

    return (
        prepared_institutions, prepared_programmes,
        prepared_subjects, prepared_historical,
    )


def _persist_catalogue(prepared):
    institutions, programmes, subjects, historical = prepared
    for _row, instance in institutions:
        instance.save()
    for _row, instance, parent in programmes:
        instance.institution = parent
        instance.save()
    for _row, instance, parent in subjects:
        instance.programme = parent
        instance.save()
    for _row, instance, parent in historical:
        instance.programme = parent
        instance.save()


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
        try:
            with transaction.atomic():
                prepared = _prepare_catalogue(by_type)
                _persist_catalogue(prepared)
                if options['dry_run']:
                    transaction.set_rollback(True)
        except (ValidationError, IntegrityError) as exc:
            raise CommandError(f'Catalogue rows failed validated persistence: {exc}') from exc
        label = 'Validated' if options['dry_run'] else 'Imported'
        self.stdout.write(self.style.SUCCESS(f'{label} {len(rows)} catalogue rows.'))
