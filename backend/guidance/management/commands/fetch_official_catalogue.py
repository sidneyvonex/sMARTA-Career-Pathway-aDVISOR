import hashlib
import json
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from accounts.official_school_data import normalize_whitespace
from guidance.official_offering_data import (
    OFFICIAL_COMBINATIONS_ENDPOINT,
    OFFICIAL_SUBJECT_CODES,
    OFFICIAL_TRACKS,
)


class Command(BaseCommand):
    help = 'Fetch the complete official Senior School combination catalogue.'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True)
        parser.add_argument('--checked-at', default=date.today().isoformat())
        parser.add_argument('--timeout', type=float, default=30)
        parser.add_argument('--delay', type=float, default=0.1)

    def handle(self, *args, **options):
        try:
            checked_at = date.fromisoformat(options['checked_at'])
        except ValueError as exc:
            raise CommandError('--checked-at must use YYYY-MM-DD.') from exc

        records = []
        track_counts = {}
        for track in OFFICIAL_TRACKS:
            payload = self._fetch(track, timeout=options['timeout'])
            rows = payload.get('data')
            if not isinstance(rows, list) or payload.get('count') != len(rows):
                raise CommandError(f'Invalid catalogue response for {track}.')
            track_counts[track] = len(rows)
            for raw in rows:
                title = normalize_whitespace(raw.get('subject_combination'))
                subjects = [normalize_whitespace(item) for item in title.split(',')]
                if len(subjects) != 3 or any(not subject for subject in subjects):
                    raise CommandError(
                        f'Combination {raw.get("subject_combination_code")} does not '
                        'contain exactly three subjects.'
                    )
                unknown = [
                    subject for subject in subjects
                    if subject not in OFFICIAL_SUBJECT_CODES
                ]
                if unknown:
                    raise CommandError(f'Unmapped official subjects: {unknown}.')
                records.append({
                    'source_record_id': normalize_whitespace(raw.get('id')),
                    'code': normalize_whitespace(
                        raw.get('subject_combination_code')
                    ).upper(),
                    'track': track,
                    'title': title,
                    'subjects': subjects,
                    'subject_codes': [
                        OFFICIAL_SUBJECT_CODES[subject] for subject in subjects
                    ],
                })
            if options['delay']:
                time.sleep(options['delay'])

        if len({row['code'] for row in records}) != len(records):
            raise CommandError('Official catalogue contains duplicate codes.')
        if len({row['source_record_id'] for row in records}) != len(records):
            raise CommandError('Official catalogue contains duplicate source IDs.')
        records.sort(key=lambda row: row['code'])
        snapshot = {
            'schema_version': 1,
            'source': {
                'publisher': 'Kenya Ministry of Education',
                'endpoint': OFFICIAL_COMBINATIONS_ENDPOINT,
                'checked_at': checked_at.isoformat(),
            },
            'track_counts': track_counts,
            'record_count': len(records),
            'records': records,
        }
        encoded = (json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n').encode(
            'utf-8'
        )
        output_path = Path(options['output']).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encoded)
        self.stdout.write(self.style.SUCCESS(
            f'Fetched {len(records)} official combinations across '
            f'{len(track_counts)} tracks.'
        ))
        self.stdout.write(f'Output: {output_path}')
        self.stdout.write(f'SHA256: {hashlib.sha256(encoded).hexdigest()}')

    def _fetch(self, track, *, timeout):
        query = urlencode({'track': track})
        request = Request(
            f'{OFFICIAL_COMBINATIONS_ENDPOINT}?{query}',
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Smarta-Shauri-school-audit/1.0',
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except Exception as exc:
            raise CommandError(f'Failed to fetch catalogue track {track}: {exc}') from exc

