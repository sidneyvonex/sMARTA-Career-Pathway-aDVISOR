import hashlib
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from guidance.models import SubjectCombination
from guidance.official_offering_data import (
    OFFICIAL_COMBINATIONS_ENDPOINT,
    OFFICIAL_SUBJECT_CODES,
)


pytestmark = pytest.mark.django_db

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_SNAPSHOT = (
    REPOSITORY_ROOT / 'data' / 'schools' / 'official-catalogue-2026-07-31.json'
)
CATALOGUE_SHA256 = (
    '9ddac3cbac55461df90b108bc4601d570495b14768998569ddd2c671760017db'
)


def test_committed_full_catalogue_integrity():
    raw = CATALOGUE_SNAPSHOT.read_bytes()
    payload = json.loads(raw)

    assert hashlib.sha256(raw).hexdigest() == CATALOGUE_SHA256
    assert payload['source']['endpoint'] == OFFICIAL_COMBINATIONS_ENDPOINT
    assert payload['source']['checked_at'] == '2026-07-31'
    assert payload['record_count'] == 511
    assert payload['track_counts'] == {
        'PURE SCIENCES': 36,
        'APPLIED SCIENCES': 86,
        'TECHNICAL STUDIES': 114,
        'LANGUAGES & LITERATURE': 80,
        'HUMANITIES & BUSINESS STUDIES': 113,
        'ARTS': 52,
        'SPORTS': 30,
    }
    records = payload['records']
    assert len({row['code'] for row in records}) == 511
    assert len({row['source_record_id'] for row in records}) == 511
    assert all(len(row['subject_codes']) == 3 for row in records)
    assert {
        subject for row in records for subject in row['subjects']
    } == set(OFFICIAL_SUBJECT_CODES)


def test_full_catalogue_import_dry_run_does_not_create_rows():
    initial_count = SubjectCombination.objects.count()

    call_command(
        'import_official_catalogue',
        source=str(CATALOGUE_SNAPSHOT),
        expected_sha256=CATALOGUE_SHA256,
    )

    assert SubjectCombination.objects.count() == initial_count

