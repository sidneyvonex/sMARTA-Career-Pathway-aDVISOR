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
    OFFICIAL_COUNTY_QUERY_VALUES,
    OFFICIAL_OFFERINGS_ENDPOINT,
    ROLLOUT_COUNTIES,
)


def identity_key(county, name):
    return county.lower(), normalize_whitespace(name).upper()


class Command(BaseCommand):
    help = 'Fetch and exactly match official offerings for rollout schools.'

    def add_arguments(self, parser):
        parser.add_argument('--schools', required=True)
        parser.add_argument('--catalogue')
        parser.add_argument('--output', required=True)
        parser.add_argument('--checked-at', default=date.today().isoformat())
        parser.add_argument('--timeout', type=float, default=30)
        parser.add_argument('--delay', type=float, default=0.1)
        parser.add_argument('--retries', type=int, default=3)
        parser.add_argument('--checkpoint-every', type=int, default=25)
        parser.add_argument('--resume', action='store_true')
        parser.add_argument(
            '--refresh-county',
            action='append',
            choices=ROLLOUT_COUNTIES,
            default=[],
        )

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

        catalogue_path = (
            Path(options['catalogue']).resolve() if options['catalogue'] else None
        )
        combinations = OFFICIAL_COMBINATIONS
        catalogue_digest = None
        if catalogue_path:
            try:
                catalogue_raw = catalogue_path.read_bytes()
                catalogue_payload = json.loads(catalogue_raw)
            except (OSError, json.JSONDecodeError) as exc:
                raise CommandError(f'Cannot read catalogue snapshot: {exc}') from exc
            combinations = {
                row['code']: {
                    'id': row['source_record_id'],
                    'title': row['title'],
                }
                for row in catalogue_payload.get('records', [])
            }
            if catalogue_payload.get('record_count') != len(combinations):
                raise CommandError('Catalogue record count does not match metadata.')
            catalogue_digest = hashlib.sha256(catalogue_raw).hexdigest()

        output_path = Path(options['output']).resolve()
        matched = []
        quarantined = []
        completed_queries = set()
        if options['resume'] and output_path.exists():
            previous = json.loads(output_path.read_text(encoding='utf-8'))
            if previous.get('source', {}).get('catalogue_snapshot_sha256') != (
                catalogue_digest
            ):
                raise CommandError('Checkpoint catalogue checksum does not match.')
            matched = previous.get('records', [])
            quarantined = previous.get('quarantined_records', [])
            completed_queries = set(previous.get('completed_queries', []))
            refresh_counties = set(options['refresh_county'])
            if refresh_counties:
                matched = [
                    row for row in matched if row['county'] not in refresh_counties
                ]
                quarantined = [
                    row for row in quarantined
                    if row['county'] not in refresh_counties
                ]
                completed_queries = {
                    query for query in completed_queries
                    if query.rsplit('|', 1)[-1] not in refresh_counties
                }

        total_queries = len(combinations) * len(ROLLOUT_COUNTIES)
        for code, combination in combinations.items():
            for county in ROLLOUT_COUNTIES:
                query_key = f'{code}|{county}'
                if query_key in completed_queries:
                    continue
                payload = self._fetch(
                    combination['id'],
                    county,
                    timeout=options['timeout'],
                    retries=options['retries'],
                )
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
                completed_queries.add(query_key)
                if (
                    options['checkpoint_every']
                    and len(completed_queries) % options['checkpoint_every'] == 0
                ):
                    self._write_snapshot(
                        output_path,
                        schools_path=schools_path,
                        catalogue_path=catalogue_path,
                        catalogue_digest=catalogue_digest,
                        checked_at=checked_at,
                        combination_count=len(combinations),
                        total_queries=total_queries,
                        completed_queries=completed_queries,
                        matched=matched,
                        quarantined=quarantined,
                        complete=False,
                    )
                    self.stdout.write(
                        f'Checkpoint: {len(completed_queries)}/{total_queries} queries; '
                        f'{len(matched)} exact, {len(quarantined)} quarantined.'
                    )
                if options['delay']:
                    time.sleep(options['delay'])

        digest = self._write_snapshot(
            output_path,
            schools_path=schools_path,
            catalogue_path=catalogue_path,
            catalogue_digest=catalogue_digest,
            checked_at=checked_at,
            combination_count=len(combinations),
            total_queries=total_queries,
            completed_queries=completed_queries,
            matched=matched,
            quarantined=quarantined,
            complete=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Fetched {len(matched)} exact offerings; quarantined '
            f'{len(quarantined)} unmatched or ambiguous records.'
        ))
        self.stdout.write(f'Output: {output_path}')
        self.stdout.write(f'SHA256: {digest}')

    def _write_snapshot(
        self,
        output_path,
        *,
        schools_path,
        catalogue_path,
        catalogue_digest,
        checked_at,
        combination_count,
        total_queries,
        completed_queries,
        matched,
        quarantined,
        complete,
    ):
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
                'catalogue_snapshot': catalogue_path.name if catalogue_path else None,
                'catalogue_snapshot_sha256': catalogue_digest,
            },
            'county_scope': list(ROLLOUT_COUNTIES),
            'combination_count': combination_count,
            'request_count': len(completed_queries),
            'expected_request_count': total_queries,
            'complete': complete,
            'completed_queries': sorted(completed_queries),
            'matched_count': len(matched),
            'quarantined_count': len(quarantined),
            'records': matched,
            'quarantined_records': quarantined,
        }
        encoded = (json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n').encode(
            'utf-8'
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
        temporary_path.write_bytes(encoded)
        temporary_path.replace(output_path)
        return hashlib.sha256(encoded).hexdigest()

    def _fetch(self, combination_id, county, *, timeout, retries=3):
        query = urlencode({
            'subject_combination_id': combination_id,
            'county': OFFICIAL_COUNTY_QUERY_VALUES[county],
        })
        request = Request(
            f'{OFFICIAL_OFFERINGS_ENDPOINT}?{query}',
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Smarta-Shauri-school-audit/1.0',
            },
        )
        for attempt in range(1, retries + 1):
            try:
                with urlopen(request, timeout=timeout) as response:
                    return json.load(response)
            except Exception as exc:
                if attempt == retries:
                    raise CommandError(
                        f'Failed to fetch offerings for {combination_id}/{county} '
                        f'after {retries} attempts: {exc}'
                    ) from exc
                time.sleep(min(attempt, 3))
