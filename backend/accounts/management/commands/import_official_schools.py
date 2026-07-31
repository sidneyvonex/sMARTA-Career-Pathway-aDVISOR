import hashlib
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import School
from accounts.official_school_data import (
    COUNTY_SUB_COUNTIES,
    OFFICIAL_DIRECTORY_URL,
    normalize_whitespace,
)


class Command(BaseCommand):
    help = 'Validate or import a dated official Ministry school snapshot.'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True)
        parser.add_argument('--expected-sha256')
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Persist changes. Without this flag the command is a dry run.',
        )

    def handle(self, *args, **options):
        source_path = Path(options['source']).resolve()
        if not source_path.is_file():
            raise CommandError(f'Source snapshot not found: {source_path}')
        encoded = source_path.read_bytes()
        digest = hashlib.sha256(encoded).hexdigest()
        expected = options.get('expected_sha256')
        if expected and digest.casefold() != expected.casefold():
            raise CommandError(
                f'Snapshot checksum mismatch: expected {expected}, got {digest}.'
            )
        try:
            snapshot = json.loads(encoded.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CommandError(f'Invalid UTF-8 JSON snapshot: {exc}') from exc

        records, checked_at = self._validate_snapshot(snapshot)
        counts = {'created': 0, 'updated': 0, 'unchanged': 0}

        with transaction.atomic():
            for record in records:
                school, created = School.objects.get_or_create(
                    source_record_id=record['source_record_id'],
                    defaults=self._school_values(record, checked_at),
                )
                if created:
                    counts['created'] += 1
                    continue

                values = self._school_values(record, checked_at)
                changed = []
                for field, value in values.items():
                    if getattr(school, field) != value:
                        setattr(school, field, value)
                        changed.append(field)
                if changed:
                    school.full_clean()
                    school.save(update_fields=changed)
                    counts['updated'] += 1
                else:
                    counts['unchanged'] += 1

            if not options['apply']:
                transaction.set_rollback(True)

        mode = 'APPLIED' if options['apply'] else 'DRY RUN'
        self.stdout.write(
            f'{mode}: {len(records)} records; '
            f'{counts["created"]} create, {counts["updated"]} update, '
            f'{counts["unchanged"]} unchanged.'
        )
        self.stdout.write(f'SHA256: {digest}')

    def _validate_snapshot(self, snapshot):
        if snapshot.get('schema_version') != 1:
            raise CommandError('Unsupported school snapshot schema version.')
        source = snapshot.get('source') or {}
        if source.get('directory_url') != OFFICIAL_DIRECTORY_URL:
            raise CommandError('Snapshot does not use the approved Ministry directory.')
        try:
            checked_at = date.fromisoformat(source['checked_at'])
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError('Snapshot has an invalid checked_at date.') from exc

        county_scope = snapshot.get('county_scope')
        if not isinstance(county_scope, list) or not county_scope:
            raise CommandError('Snapshot county_scope must be a non-empty list.')
        invalid_counties = set(county_scope) - set(COUNTY_SUB_COUNTIES)
        if invalid_counties:
            raise CommandError(
                f'Snapshot contains unsupported counties: '
                f'{", ".join(sorted(invalid_counties))}.'
            )

        records = snapshot.get('records')
        if not isinstance(records, list):
            raise CommandError('Snapshot records must be a list.')
        if snapshot.get('record_count') != len(records):
            raise CommandError('Snapshot record_count does not match records.')

        seen_ids = set()
        for record in records:
            source_record_id = normalize_whitespace(record.get('source_record_id'))
            name = normalize_whitespace(record.get('name'))
            county = record.get('county')
            if not source_record_id or not name or county not in county_scope:
                raise CommandError('Snapshot contains an invalid school record.')
            if source_record_id in seen_ids:
                raise CommandError(
                    f'Duplicate source_record_id: {source_record_id}.'
                )
            seen_ids.add(source_record_id)
        return records, checked_at

    def _school_values(self, record, checked_at):
        sub_counties = sorted(set(record.get('sub_counties') or []))
        sub_county = '; '.join(sub_counties)
        if len(sub_county) > 100:
            raise CommandError(
                f'Sub-county value is too long for {record["source_record_id"]}.'
            )
        return {
            'name': normalize_whitespace(record['name']),
            'county': record['county'],
            'sub_county': sub_county,
            'gender': normalize_whitespace(record.get('gender')).upper(),
            'cluster': normalize_whitespace(record.get('cluster')).upper(),
            'institution_type': normalize_whitespace(
                record.get('institution_type')
            ).upper(),
            'accommodation_type': normalize_whitespace(
                record.get('accommodation_type')
            ).upper(),
            'school_category': normalize_whitespace(
                record.get('school_category')
            ).upper(),
            'verification_status': School.VERIFICATION_VERIFIED,
            'source_url': OFFICIAL_DIRECTORY_URL,
            'source_checked_at': checked_at,
        }

