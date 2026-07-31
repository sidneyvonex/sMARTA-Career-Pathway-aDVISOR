import hashlib
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from guidance.models import FrameworkVersion, PathwayTrack, SubjectCombination
from guidance.official_offering_data import (
    OFFICIAL_CATALOGUE_URL,
    OFFICIAL_COMBINATIONS_ENDPOINT,
    OFFICIAL_TRACKS,
)
from students.models import Subject


class Command(BaseCommand):
    help = 'Import the complete official combination catalogue; dry-run by default.'

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
            raise CommandError(f'Cannot read catalogue snapshot: {exc}') from exc
        digest = hashlib.sha256(raw).hexdigest()
        if options['expected_sha256'] and digest != options['expected_sha256'].lower():
            raise CommandError('Catalogue snapshot checksum mismatch.')
        if payload.get('schema_version') != 1:
            raise CommandError('Unsupported catalogue snapshot schema.')
        if payload.get('source', {}).get('endpoint') != OFFICIAL_COMBINATIONS_ENDPOINT:
            raise CommandError('Unexpected catalogue source endpoint.')
        records = payload.get('records')
        if not isinstance(records, list) or payload.get('record_count') != len(records):
            raise CommandError('Catalogue record count does not match metadata.')
        try:
            checked_at = date.fromisoformat(payload['source']['checked_at'])
        except (KeyError, ValueError) as exc:
            raise CommandError('Invalid catalogue checked date.') from exc

        framework = FrameworkVersion.objects.current()
        if framework is None:
            raise CommandError('No active guidance framework exists.')
        tracks = {
            track.code: track
            for track in PathwayTrack.objects.filter(framework_version=framework)
        }
        missing_tracks = set(OFFICIAL_TRACKS.values()) - tracks.keys()
        if missing_tracks:
            raise CommandError(f'Missing pathway tracks: {sorted(missing_tracks)}.')
        required_subjects = {
            code for row in records for code in row.get('subject_codes', [])
        }
        subjects = {
            subject.code: subject
            for subject in Subject.objects.filter(code__in=required_subjects)
        }
        if missing_subjects := required_subjects - subjects.keys():
            raise CommandError(f'Missing Grade 10 subjects: {sorted(missing_subjects)}.')
        for row in records:
            if len(row.get('subject_codes', [])) != 3:
                raise CommandError(f'{row.get("code")} does not have three subjects.')
            if row.get('track') not in OFFICIAL_TRACKS:
                raise CommandError(f'Unknown track for {row.get("code")}.')

        if not options['apply']:
            self.stdout.write(
                f'Dry run: {len(records)} official combinations are ready to import.'
            )
            return

        created = updated = 0
        seen_codes = set()
        with transaction.atomic():
            framework.title = 'CBC Senior School Subject Combination Catalogue 2026'
            framework.description = (
                'Official Senior School subject combinations, with verified school '
                'availability limited to the current five-county project rollout.'
            )
            framework.source_url = OFFICIAL_CATALOGUE_URL
            framework.save(update_fields=['title', 'description', 'source_url', 'updated_at'])
            for row in records:
                subject_one, subject_two, subject_three = (
                    subjects[code] for code in row['subject_codes']
                )
                _, was_created = SubjectCombination.objects.update_or_create(
                    framework_version=framework,
                    code=row['code'],
                    defaults={
                        'track': tracks[OFFICIAL_TRACKS[row['track']]],
                        'title': row['title'].replace(',', ', '),
                        'description': 'Official Senior School subject combination.',
                        'subject_one': subject_one,
                        'subject_two': subject_two,
                        'subject_three': subject_three,
                        'is_active': True,
                        'verification_status': (
                            SubjectCombination.VERIFICATION_VERIFIED
                        ),
                        'source_url': OFFICIAL_CATALOGUE_URL,
                        'source_checked_at': checked_at,
                    },
                )
                seen_codes.add(row['code'])
                created += int(was_created)
                updated += int(not was_created)
            SubjectCombination.objects.filter(
                framework_version=framework,
            ).exclude(code__in=seen_codes).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(
            f'Imported {len(records)} official combinations '
            f'({created} created, {updated} updated).'
        ))

