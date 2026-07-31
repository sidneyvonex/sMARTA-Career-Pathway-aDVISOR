import hashlib
import io
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command

from accounts.models import School
from accounts.official_school_data import OFFICIAL_DIRECTORY_URL


pytestmark = pytest.mark.django_db

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_FIVE_COUNTY_SNAPSHOT = (
    REPOSITORY_ROOT / 'data' / 'schools' / 'official-schools-2026-07-31.json'
)
OFFICIAL_FIVE_COUNTY_SHA256 = (
    '25b3fcd66bd898a2db7a2715bc15bb9983f84df8f2f90232503a59a5d0a521a6'
)


def snapshot(records):
    return {
        'schema_version': 1,
        'source': {
            'publisher': 'Kenya Ministry of Education',
            'directory_url': OFFICIAL_DIRECTORY_URL,
            'search_endpoint': (
                'https://selection.education.go.ke/api/open/school-search'
            ),
            'checked_at': '2026-07-31',
        },
        'county_scope': ['kiambu'],
        'request_count': 15,
        'record_count': len(records),
        'records': records,
    }


def official_record(name='MUNYU MIXED SEC SCH'):
    return {
        'source_record_id': '34e55ac9-c200-456d-a960-d41996328536',
        'name': name,
        'county': 'kiambu',
        'sub_counties': ['Thika East'],
        'gender': 'MIXED',
        'cluster': 'C4',
        'institution_type': 'PUBLIC',
        'accommodation_type': '',
        'school_category': '',
        'knec_code': None,
    }


def write_snapshot(tmp_path, payload):
    path = tmp_path / 'official-schools.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return path


def test_committed_five_county_snapshot_integrity():
    raw = OFFICIAL_FIVE_COUNTY_SNAPSHOT.read_bytes()
    payload = json.loads(raw)

    assert hashlib.sha256(raw).hexdigest() == OFFICIAL_FIVE_COUNTY_SHA256
    assert payload['source']['directory_url'] == OFFICIAL_DIRECTORY_URL
    assert payload['source']['checked_at'] == '2026-07-31'
    assert payload['request_count'] == 49
    assert payload['record_count'] == 1253
    assert payload['county_scope'] == [
        'kiambu',
        'muranga',
        'nyeri',
        'kirinyaga',
        'nyandarua',
    ]

    records = payload['records']
    assert len({record['source_record_id'] for record in records}) == 1253
    assert all(record['knec_code'] is None for record in records)
    assert {
        county: sum(record['county'] == county for record in records)
        for county in payload['county_scope']
    } == {
        'kiambu': 334,
        'kirinyaga': 158,
        'muranga': 341,
        'nyandarua': 194,
        'nyeri': 226,
    }


def test_import_is_dry_run_by_default(tmp_path):
    source = write_snapshot(tmp_path, snapshot([official_record()]))

    call_command('import_official_schools', source=str(source))

    assert not School.objects.filter(source_record_id__isnull=False).exists()


def test_import_creates_verified_identity_without_fabricating_knec_code(tmp_path):
    source = write_snapshot(tmp_path, snapshot([official_record()]))

    call_command('import_official_schools', source=str(source), apply=True)

    school = School.objects.get(
        source_record_id='34e55ac9-c200-456d-a960-d41996328536'
    )
    assert school.name == 'MUNYU MIXED SEC SCH'
    assert school.school_code is None
    assert school.county == 'kiambu'
    assert school.sub_county == 'Thika East'
    assert school.verification_status == School.VERIFICATION_VERIFIED
    assert school.source_url == OFFICIAL_DIRECTORY_URL
    assert school.source_checked_at == date(2026, 7, 31)


def test_import_is_idempotent_and_updates_changed_identity(tmp_path):
    first = write_snapshot(tmp_path, snapshot([official_record()]))
    call_command('import_official_schools', source=str(first), apply=True)
    updated = write_snapshot(
        tmp_path,
        snapshot([official_record(name='MUNYU MIXED SECONDARY SCHOOL')]),
    )

    call_command('import_official_schools', source=str(updated), apply=True)

    assert School.objects.filter(source_record_id__isnull=False).count() == 1
    assert School.objects.get(source_record_id__isnull=False).name == (
        'MUNYU MIXED SECONDARY SCHOOL'
    )


def test_import_rejects_checksum_mismatch(tmp_path):
    source = write_snapshot(tmp_path, snapshot([official_record()]))

    with pytest.raises(Exception, match='checksum mismatch'):
        call_command(
            'import_official_schools',
            source=str(source),
            expected_sha256='0' * 64,
        )


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_fetch_uses_uppercase_queries_and_deduplicates_ids(tmp_path):
    requested_urls = []

    def fake_urlopen(request, timeout):
        requested_urls.append(request.full_url)
        payload = {
            'success': True,
            'schools': [{
                'id': 'official-id',
                'institution_name': '  Test   School ',
                'gender': 'mixed',
                'cluster': 'c4',
                'institution_type': 'public',
            }],
        }
        return FakeResponse(json.dumps(payload).encode('utf-8'))

    output = tmp_path / 'fetched.json'
    with patch(
        'accounts.management.commands.fetch_official_schools.urlopen',
        side_effect=fake_urlopen,
    ):
        call_command(
            'fetch_official_schools',
            output=str(output),
            counties=['kiambu'],
            checked_at='2026-07-31',
            delay=0,
        )

    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['record_count'] == 1
    assert payload['records'][0]['name'] == 'Test School'
    assert len(payload['records'][0]['sub_counties']) == 15
    assert all('sub_county=' in url for url in requested_urls)
    assert any('THIKA+EAST' in url for url in requested_urls)
    assert hashlib.sha256(output.read_bytes()).hexdigest()
