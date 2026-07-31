import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command

from accounts.models import School
from guidance.models import SchoolOffering, SubjectCombination
from guidance.official_offering_data import OFFICIAL_OFFERINGS_ENDPOINT


pytestmark = pytest.mark.django_db

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_OFFERING_SNAPSHOT = (
    REPOSITORY_ROOT / 'data' / 'schools' / 'official-offerings-2026-07-31.json'
)
OFFICIAL_OFFERING_SHA256 = (
    '25e316202d3c1ec060c13dc72d8310e91fbd5de0d39320a631b74b2e3681ffdc'
)


def offering_snapshot(source_record_id):
    return {
        'schema_version': 1,
        'source': {
            'publisher': 'Kenya Ministry of Education',
            'endpoint': OFFICIAL_OFFERINGS_ENDPOINT,
            'checked_at': '2026-07-31',
            'school_snapshot': 'schools.json',
            'school_snapshot_sha256': '0' * 64,
        },
        'county_scope': ['kiambu'],
        'combination_count': 1,
        'request_count': 1,
        'matched_count': 1,
        'quarantined_count': 0,
        'records': [{
            'combination_code': 'ST1042',
            'combination_source_id': '0cecfbd4-be11-4b36-afbf-9461b3f4f2c0',
            'school_source_record_id': source_record_id,
            'school_name': 'TEST SCHOOL',
            'county': 'kiambu',
            'gender': 'MIXED',
            'cluster': 'C4',
            'accommodation_type': 'DAY',
            'school_category': 'REGULAR',
        }],
        'quarantined_records': [],
    }


def write_snapshot(tmp_path, payload):
    source = tmp_path / 'offerings.json'
    source.write_text(json.dumps(payload), encoding='utf-8')
    return source


def test_committed_offering_snapshot_integrity():
    raw = OFFICIAL_OFFERING_SNAPSHOT.read_bytes()
    payload = json.loads(raw)

    assert hashlib.sha256(raw).hexdigest() == OFFICIAL_OFFERING_SHA256
    assert payload['source']['endpoint'] == OFFICIAL_OFFERINGS_ENDPOINT
    assert payload['source']['checked_at'] == '2026-07-31'
    assert payload['combination_count'] == 10
    assert payload['request_count'] == 50
    assert payload['matched_count'] == 623
    assert payload['quarantined_count'] == 0
    assert len(payload['records']) == 623
    assert len({
        (row['school_source_record_id'], row['combination_code'])
        for row in payload['records']
    }) == 623


def test_offering_import_is_dry_run_by_default(tmp_path):
    school = School.objects.create(
        name='TEST SCHOOL',
        county='kiambu',
        source_record_id='school-id',
    )
    source = write_snapshot(tmp_path, offering_snapshot(school.source_record_id))

    call_command('import_official_offerings', source=str(source))

    assert not SchoolOffering.objects.filter(school=school).exists()


def test_offering_import_applies_verified_evidence_idempotently(tmp_path):
    school = School.objects.create(
        name='TEST SCHOOL',
        county='kiambu',
        source_record_id='school-id',
    )
    source = write_snapshot(tmp_path, offering_snapshot(school.source_record_id))

    call_command('import_official_offerings', source=str(source), apply=True)
    call_command('import_official_offerings', source=str(source), apply=True)

    offering = SchoolOffering.objects.get(
        school=school,
        combination=SubjectCombination.objects.get(code='ST1042'),
    )
    assert offering.verification_status == SchoolOffering.VERIFICATION_VERIFIED
    assert offering.source_checked_at.isoformat() == '2026-07-31'
    school.refresh_from_db()
    assert school.accommodation_type == 'DAY'
    assert school.school_category == 'REGULAR'


def test_fetch_quarantines_non_exact_school_names(tmp_path):
    schools = tmp_path / 'schools.json'
    schools.write_text(json.dumps({
        'records': [{
            'source_record_id': 'school-id',
            'name': 'EXACT SCHOOL',
            'county': 'kiambu',
        }],
    }), encoding='utf-8')
    output = tmp_path / 'offerings.json'
    response = {
        'message': 'success',
        'subject_combination': 'Agriculture,Biology,Chemistry',
        'response': [{
            'senior_school_name': 'SIMILAR SCHOOL',
            'county': 'KIAMBU',
            'gender': 'MIXED',
            'cluster': 'C4',
            'accomodation_type': 'DAY',
            'category': 'REGULAR',
        }],
    }

    with patch(
        'guidance.management.commands.fetch_official_offerings.Command._fetch',
        return_value=response,
    ), patch(
        'guidance.management.commands.fetch_official_offerings.OFFICIAL_COMBINATIONS',
        {'ST1042': {
            'id': 'combination-id',
            'track': 'PURE SCIENCES',
            'title': 'Agriculture,Biology,Chemistry',
        }},
    ), patch(
        'guidance.management.commands.fetch_official_offerings.ROLLOUT_COUNTIES',
        ('kiambu',),
    ):
        call_command(
            'fetch_official_offerings',
            schools=str(schools),
            output=str(output),
            checked_at='2026-07-31',
            delay=0,
        )

    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['matched_count'] == 0
    assert payload['quarantined_count'] == 1
    assert payload['quarantined_records'][0]['reason'] == (
        'no_exact_identity_match'
    )

