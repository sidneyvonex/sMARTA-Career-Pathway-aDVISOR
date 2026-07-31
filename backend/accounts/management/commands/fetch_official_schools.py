import hashlib
import json
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from accounts.official_school_data import (
    COUNTY_SUB_COUNTIES,
    OFFICIAL_DIRECTORY_URL,
    OFFICIAL_SEARCH_ENDPOINT,
    normalize_whitespace,
)


class Command(BaseCommand):
    help = 'Fetch a dated Ministry school-identity snapshot for rollout counties.'

    def add_arguments(self, parser):
        parser.add_argument('--output', required=True)
        parser.add_argument(
            '--county',
            action='append',
            choices=tuple(COUNTY_SUB_COUNTIES),
            dest='counties',
        )
        parser.add_argument('--checked-at', default=date.today().isoformat())
        parser.add_argument('--timeout', type=float, default=30)
        parser.add_argument('--delay', type=float, default=0.1)

    def handle(self, *args, **options):
        try:
            checked_at = date.fromisoformat(options['checked_at'])
        except ValueError as exc:
            raise CommandError('--checked-at must use YYYY-MM-DD.') from exc

        counties = options['counties'] or list(COUNTY_SUB_COUNTIES)
        records_by_id = {}
        requests_made = 0

        for county in counties:
            for sub_county in COUNTY_SUB_COUNTIES[county]:
                payload = self._fetch_sub_county(
                    sub_county,
                    timeout=options['timeout'],
                )
                requests_made += 1
                for raw_school in payload:
                    self._merge_school(
                        records_by_id,
                        raw_school,
                        county=county,
                        sub_county=sub_county,
                    )
                if options['delay']:
                    time.sleep(options['delay'])

        records = sorted(
            records_by_id.values(),
            key=lambda item: (item['county'], item['name'], item['source_record_id']),
        )
        snapshot = {
            'schema_version': 1,
            'source': {
                'publisher': 'Kenya Ministry of Education',
                'directory_url': OFFICIAL_DIRECTORY_URL,
                'search_endpoint': OFFICIAL_SEARCH_ENDPOINT,
                'checked_at': checked_at.isoformat(),
            },
            'county_scope': list(counties),
            'request_count': requests_made,
            'record_count': len(records),
            'records': records,
        }
        encoded = (
            json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n'
        ).encode('utf-8')
        output_path = Path(options['output']).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encoded)
        digest = hashlib.sha256(encoded).hexdigest()

        self.stdout.write(self.style.SUCCESS(
            f'Fetched {len(records)} unique schools from {requests_made} '
            f'sub-county queries.'
        ))
        self.stdout.write(f'Output: {output_path}')
        self.stdout.write(f'SHA256: {digest}')

    def _fetch_sub_county(self, sub_county, *, timeout):
        # The live Ministry endpoint currently matches uppercase values only.
        query = urlencode({'sub_county': sub_county.upper()})
        request = Request(
            f'{OFFICIAL_SEARCH_ENDPOINT}?{query}',
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Smarta-Shauri-school-audit/1.0',
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.load(response)
        except Exception as exc:
            raise CommandError(
                f'Failed to fetch Ministry schools for {sub_county}: {exc}'
            ) from exc

        if payload.get('success') is not True:
            raise CommandError(
                f'Ministry response was unsuccessful for {sub_county}.'
            )
        schools = payload.get('schools')
        if not isinstance(schools, list):
            raise CommandError(
                f'Ministry response did not contain a school list for {sub_county}.'
            )
        return schools

    def _merge_school(self, records_by_id, raw, *, county, sub_county):
        source_record_id = normalize_whitespace(raw.get('id'))
        name = normalize_whitespace(raw.get('institution_name'))
        if not source_record_id or not name:
            raise CommandError(
                f'Ministry record in {sub_county} lacks an ID or school name.'
            )

        candidate = {
            'source_record_id': source_record_id,
            'name': name,
            'county': county,
            'sub_counties': [sub_county],
            'gender': normalize_whitespace(raw.get('gender')).upper(),
            'cluster': normalize_whitespace(raw.get('cluster')).upper(),
            'institution_type': normalize_whitespace(
                raw.get('institution_type')
            ).upper(),
            'accommodation_type': '',
            'school_category': '',
            'knec_code': None,
        }
        existing = records_by_id.get(source_record_id)
        if existing is None:
            records_by_id[source_record_id] = candidate
            return

        comparable_fields = (
            'name',
            'county',
            'gender',
            'cluster',
            'institution_type',
        )
        conflicts = [
            field for field in comparable_fields
            if existing[field] != candidate[field]
        ]
        if conflicts:
            raise CommandError(
                f'Conflicting Ministry record {source_record_id}: '
                f'{", ".join(conflicts)}.'
            )
        if sub_county not in existing['sub_counties']:
            existing['sub_counties'].append(sub_county)
            existing['sub_counties'].sort()
