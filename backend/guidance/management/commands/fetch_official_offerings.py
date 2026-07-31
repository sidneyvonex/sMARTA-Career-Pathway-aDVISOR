import hashlib
import json
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from accounts.official_school_data import normalize_whitespace
from guidance.official_offering_data import (
    OFFICIAL_COMBINATIONS,
    OFFICIAL_OFFERINGS_ENDPOINT,
    ROLLOUT_COUNTIES,
)


def identity_key(county, name):
    return county.lower(), normalize_whitespace(name).upper()


class Command(BaseCommand):
    help = 'Fetch and exactly match official offerings for rollout schools.'

    def add_arguments(self, parser):
        parser.add_argument('--schools', required=True)
        parser.add_argument('--output', required=True)
        parser.add_argument('--checked-at', default=date.today().isoformat())
        parser.add_argument('--timeout', type=float, default=30)
        parser.add_argument('--delay', type=float, default=0.1)

    def handle(self, *args, **options):
        try:
            checked_at = date.fromisoformat(options['checked_at'])
        except ValueError as exc:
            raise CommandError('--checked-at must use YYYY-MM-DD.') from exc

        schools_path = Path(options['schools']).resolve()
        try:
            schools_payload = json.loads(schools_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'Cannot read school snapshot: {exc}') from exc

        school_index = defaultdict(list)
        for school in schools_payload.get('records', []):
            school_index[identity_key(school['county'], school['name'])].append(school)

        matched = []
        quarantined = []
        requests_made = 0
        for code, combination in OFFICIAL_COMBINATIONS.items():
            for county in ROLLOUT_COUNTIES:
                payload = self._fetch(
                    combination['id'], county, timeout=options['timeout']
                )
                requests_made += 1
                if payload.get('message') != 'success':
                    raise CommandError(f'Unsuccessful offering response for {code}/{county}.')
                if payload.get('subject_combination') != combination['title']:
                    raise CommandError(f'Combination title changed for {code}.')

                for raw in payload.get('response', []):
                    name = normalize_whitespace(raw.get('senior_school_name'))
                    candidates = school_index[identity_key(county, name)]
                    record = {
                        'combination_code': code,
                        'combination_source_id': combination['id'],
                        'school_name': name,
                        'county': county,
                        'gender': normalize_whitespace(raw.get('gender')).upper(),
                        'cluster': normalize_whitespace(raw.get('cluster')).upper(),
                        'accommodation_type': normalize_whitespace(
                            raw.get('accomodation_type')
                        ).upper(),
                        'school_category': normalize_whitespace(
                            raw.get('category')
                        ).upper(),
                    }
                    if len(candidates) == 1:
                        record['school_source_record_id'] = candidates[0][
                            'source_record_id'
                        ]
                        matched.append(record)
                    else:
                        record['reason'] = (
                            'no_exact_identity_match'
                            if not candidates else 'ambiguous_identity_match'
                        )
                        quarantined.append(record)
                if options['delay']:
                    time.sleep(options['delay'])

        matched.sort(key=lambda row: (
            row['combination_code'], row['county'], row['school_name']
        ))
        quarantined.sort(key=lambda row: (
            row['combination_code'], row['county'], row['school_name']
        ))
        snapshot = {
            'schema_version': 1,
            'source': {
                'publisher': 'Kenya Ministry of Education',
                'endpoint': OFFICIAL_OFFERINGS_ENDPOINT,
                'checked_at': checked_at.isoformat(),
                'school_snapshot': schools_path.name,
                'school_snapshot_sha256': hashlib.sha256(
                    schools_path.read_bytes()
                ).hexdigest(),
            },
            'county_scope': list(ROLLOUT_COUNTIES),
            'combination_count': len(OFFICIAL_COMBINATIONS),
            'request_count': requests_made,
            'matched_count': len(matched),
            'quarantined_count': len(quarantined),
            'records': matched,
            'quarantined_records': quarantined,
        }
        encoded = (json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n').encode(
            'utf-8'
        )
        output_path = Path(options['output']).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encoded)
        self.stdout.write(self.style.SUCCESS(
            f'Fetched {len(matched)} exact offerings; quarantined '
            f'{len(quarantined)} unmatched or ambiguous records.'
        ))
        self.stdout.write(f'Output: {output_path}')
        self.stdout.write(f'SHA256: {hashlib.sha256(encoded).hexdigest()}')

    def _fetch(self, combination_id, county, *, timeout):
        query = urlencode({
            'subject_combination_id': combination_id,
            'county': county.upper(),
        })
        request = Request(
            f'{OFFICIAL_OFFERINGS_ENDPOINT}?{query}',
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Smarta-Shauri-school-audit/1.0',
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except Exception as exc:
            raise CommandError(
                f'Failed to fetch offerings for {combination_id}/{county}: {exc}'
            ) from exc

