import hashlib
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import School
from guidance.models import SchoolOffering, SubjectCombination
from guidance.official_offering_data import OFFICIAL_OFFERINGS_ENDPOINT


class Command(BaseCommand):
    help = 'Import exact-match official school offerings; dry-run by default.'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True)
        parser.add_argument('--expected-sha256')
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        source = Path(options['source']).resolve()
        try:
            raw = source.read_bytes()
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'Cannot read offering snapshot: {exc}') from exc

        digest = hashlib.sha256(raw).hexdigest()
        if options['expected_sha256'] and digest != options['expected_sha256'].lower():
            raise CommandError('Offering snapshot checksum mismatch.')
        if payload.get('schema_version') != 1:
            raise CommandError('Unsupported offering snapshot schema.')
        if payload.get('source', {}).get('endpoint') != OFFICIAL_OFFERINGS_ENDPOINT:
            raise CommandError('Unexpected offering source endpoint.')
        records = payload.get('records')
        if not isinstance(records, list) or payload.get('matched_count') != len(records):
            raise CommandError('Offering record count does not match metadata.')
        try:
            checked_at = date.fromisoformat(payload['source']['checked_at'])
        except (KeyError, ValueError) as exc:
            raise CommandError('Invalid offering checked date.') from exc

        school_ids = {row['school_source_record_id'] for row in records}
        combination_codes = {row['combination_code'] for row in records}
        schools = {
            school.source_record_id: school
            for school in School.objects.filter(source_record_id__in=school_ids)
        }
        combinations = {
            combination.code: combination
            for combination in SubjectCombination.objects.filter(
                code__in=combination_codes
            )
        }
        if missing := school_ids - schools.keys():
            raise CommandError(f'{len(missing)} referenced schools are not imported.')
        if missing := combination_codes - combinations.keys():
            raise CommandError(f'Missing subject combinations: {sorted(missing)}.')

        if not options['apply']:
            self.stdout.write(
                f'Dry run: {len(records)} verified offerings are ready to import.'
            )
            return

        created = updated = 0
        source_url = 'https://selection.education.go.ke/pathways'
        with transaction.atomic():
            for row in records:
                school = schools[row['school_source_record_id']]
                _, was_created = SchoolOffering.objects.update_or_create(
                    school=school,
                    combination=combinations[row['combination_code']],
                    defaults={
                        'is_active': True,
                        'verification_status': SchoolOffering.VERIFICATION_VERIFIED,
                        'source_url': source_url,
                        'source_checked_at': checked_at,
                    },
                )
                created += int(was_created)
                updated += int(not was_created)
                School.objects.filter(pk=school.pk).update(
                    accommodation_type=row['accommodation_type'],
                    school_category=row['school_category'],
                )
        self.stdout.write(self.style.SUCCESS(
            f'Imported {len(records)} verified offerings '
            f'({created} created, {updated} updated).'
        ))

