import pytest
from rest_framework.test import APIClient

from students.models import PerformanceLevelDefinition
from students import progress
from students.progress import derive_continuity_progress, derive_progress_for_enrolments
from tests.factories import (
    CBCGradeFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    SubjectFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db

PROGRESS_URL = '/api/v1/students/progress/'


def evidence(
    identifier,
    level,
    rank,
    *,
    academic_grade=10,
    year=2026,
    term=1,
    verified=False,
    me2_rank=5,
):
    """A hand-built evidence snapshot; changing a rule branch must fail a case."""
    return {
        'id': identifier,
        'academic_grade': academic_grade,
        'year': year,
        'term': term,
        'level': level,
        'rank': rank,
        'me2_rank': me2_rank,
        'framework': {'code': 'CBC-SENIOR-SCHOOL', 'version': 'pilot-v1'},
        'source': 'school' if verified else 'learner',
        'verified_at': '2026-01-01T00:00:00Z' if verified else None,
        'verified_school': 9 if verified else None,
        'verified_by': 7 if verified else None,
        'created_at': f'2026-01-{identifier:02d}T00:00:00Z',
    }


@pytest.mark.parametrize(
    ('records', 'expected_rule', 'expected_status', 'used_ids'),
    [
        ([], 'missing_evidence', 'insufficient_evidence', []),
        ([evidence(1, 'BE1', 2)], 'latest_be_support', 'support', [1]),
        ([evidence(1, 'ME1', 6)], 'one_non_be_insufficient', 'insufficient_evidence', [1]),
        (
            [evidence(1, 'ME1', 6), evidence(2, 'AE1', 4, term=2)],
            'latest_ae_or_two_declines_attention',
            'needs_attention',
            [2],
        ),
        (
            [evidence(1, 'ME1', 6), evidence(2, 'BE1', 2, term=2)],
            'latest_be_support',
            'support',
            [2],
        ),
        (
            [evidence(1, 'AE1', 4), evidence(2, 'AE2', 3, term=2)],
            'two_ae_be_support',
            'support',
            [1, 2],
        ),
        (
            [
                evidence(1, 'ME1', 6),
                evidence(2, 'ME1', 6, term=2),
                evidence(3, 'ME1', 6, term=3),
            ],
            'otherwise_me_on_track',
            'on_track',
            [3],
        ),
        (
            [
                evidence(1, 'EE2', 7),
                evidence(2, 'ME1', 6, term=2),
                evidence(3, 'ME2', 5, term=3),
            ],
            'latest_ae_or_two_declines_attention',
            'needs_attention',
            [1, 2, 3],
        ),
        (
            [evidence(1, 'ME1', 6), evidence(2, 'EE2', 7, term=2)],
            'latest_ee_or_improving_to_me2_strong',
            'strong',
            [2],
        ),
        (
            [evidence(1, 'AE1', 4), evidence(2, 'ME2', 5, term=2)],
            'latest_ee_or_improving_to_me2_strong',
            'strong',
            [1, 2],
        ),
        (
            [evidence(1, 'ME1', 6), evidence(2, 'ME2', 5, term=2)],
            'otherwise_me_on_track',
            'on_track',
            [2],
        ),
    ],
)
def test_derivation_stops_at_the_first_matching_rule(
    records, expected_rule, expected_status, used_ids
):
    """Catches a reordered or non-short-circuit precedence table."""
    result = derive_continuity_progress('MTH', 'Mathematics', records)

    assert result['rule_code'] == expected_rule
    assert result['status'] == expected_status
    assert [record['id'] for record in result['records_used']] == used_ids


def test_derivation_orders_cross_grade_evidence_before_evaluating_the_latest_rule():
    """Catches using insertion order or term alone instead of mandated chronology."""
    result = derive_continuity_progress(
        'ENG',
        'English',
        [
            evidence(3, 'BE1', 2, academic_grade=11, year=2026, term=1),
            evidence(1, 'ME1', 6, academic_grade=10, year=2030, term=3),
            evidence(2, 'EE1', 8, academic_grade=10, year=2031, term=1),
        ],
    )

    assert result['rule_code'] == 'latest_be_support'
    assert [record['id'] for record in result['evidence']] == [1, 2, 3]


def test_improving_to_me2_uses_the_latest_framework_rank_threshold():
    """Catches treating the pilot's ME2 rank as a cross-framework constant."""
    result = derive_continuity_progress(
        'KIS',
        'Kiswahili',
        [
            evidence(1, 'AE1', 6),
            evidence(2, 'ME1', 7, term=2, me2_rank=8),
        ],
    )

    assert result['rule_code'] == 'otherwise_me_on_track'


@pytest.mark.parametrize(
    ('records', 'expected_confidence'),
    [
        ([evidence(1, 'BE1', 2, verified=True)], 'school_verified'),
        ([evidence(1, 'ME1', 6)], 'learner_entered'),
        (
            [evidence(1, 'AE1', 4, verified=True), evidence(2, 'ME2', 5, term=2)],
            'mixed',
        ),
    ],
)
def test_confidence_reflects_only_the_evidence_used_by_the_winning_rule(
    records, expected_confidence
):
    """Catches treating a source label or unused history as verified provenance."""
    result = derive_continuity_progress('SCI', 'Science', records)

    assert result['evidence_confidence'] == expected_confidence


def test_api_groups_historical_evidence_by_continuity_and_reports_current_subjects_once():
    """Catches losing archived history or returning duplicate continuity rows."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    historical = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(code='MAT9', continuity_code='MAT', grade=9),
    )
    historical.archive()
    current = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(code='MAT10', continuity_code='MAT', grade=10),
    )
    CBCGradeFactory(student_subject=historical, level='AE1', term=3, year=2025)
    CBCGradeFactory(student_subject=current, level='ME2', term=1, year=2026)

    client = APIClient()
    client.force_authenticate(profile.user)
    response = client.get(PROGRESS_URL)

    assert response.status_code == 200
    data = response.data['data']
    assert len(data['subjects']) == 1
    assert data['subjects'][0]['continuity_code'] == 'MAT'
    assert [item['academic_grade'] for item in data['subjects'][0]['evidence']] == [9, 10]
    assert data['subjects'][0]['rule_code'] == 'latest_ee_or_improving_to_me2_strong'


def test_api_returns_explainable_snapshots_and_no_numeric_readiness_field():
    """Catches a non-reproducible explanation or prohibited scoring/percentage output."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    enrollment = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(code='PHY10', continuity_code='PHY', grade=10),
    )
    grade = CBCGradeFactory(student_subject=enrollment, level='BE2')
    PerformanceLevelDefinition.objects.filter(
        framework=grade.framework,
        code='ME2',
    ).update(rank=9)
    client = APIClient()
    client.force_authenticate(profile.user)

    response = client.get(PROGRESS_URL)

    assert response.status_code == 200
    subject = response.data['data']['subjects'][0]
    assert set(subject) == {
        'continuity_code', 'subject_name', 'status', 'label', 'rule_code',
        'explanation', 'suggested_action', 'evidence_confidence', 'records_used',
        'evidence', 'decision_inputs',
    }
    assert subject['records_used'][0]['id'] == grade.id
    assert subject['records_used'][0]['framework']['code'] == 'CBC-SENIOR-SCHOOL'
    assert subject['decision_inputs'] == {
        'latest_framework': {
            'code': grade.framework.code,
            'version': grade.framework.version,
        },
        'me2_rank': 9,
    }
    assert {'status', 'subject_continuity_codes', 'label'} == set(response.data['data']['overall'])
    assert 'advisory_disclaimer' in response.data['data']
    assert 'percentage' not in str(response.data['data']).casefold()
    assert 'raw_score' not in str(response.data['data']).casefold()
    assert 'aggregate' not in response.data['data']
    assert 'admission' not in response.data['data']


def test_service_rejects_evidence_with_a_missing_framework_level_definition():
    """Catches silently discarding evidence from an incomplete framework."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    enrollment = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(code='CFG10', continuity_code='CFG', grade=10),
    )
    grade = CBCGradeFactory(student_subject=enrollment, level='ME1')
    PerformanceLevelDefinition.objects.filter(
        framework=grade.framework,
        code='ME1',
    ).delete()

    with pytest.raises(progress.ProgressConfigurationError) as error:
        derive_progress_for_enrolments([enrollment])

    assert error.value.context == {
        'framework_code': grade.framework.code,
        'framework_version': grade.framework.version,
        'level': 'ME1',
    }


def test_api_fails_closed_when_the_latest_evidence_level_is_not_defined():
    """Catches returning a partial progress status after configuration loss."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    enrollment = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(code='ERR10', continuity_code='ERR', grade=10),
    )
    grade = CBCGradeFactory(student_subject=enrollment, level='ME1')
    PerformanceLevelDefinition.objects.filter(
        framework=grade.framework,
        code='ME1',
    ).delete()
    client = APIClient()
    client.force_authenticate(profile.user)

    response = client.get(PROGRESS_URL)

    assert response.status_code == 500
    assert response.data == {
        'data': None,
        'error': True,
        'message': (
            'Academic progress is temporarily unavailable because an assessment '
            'framework configuration is incomplete.'
        ),
    }


def test_api_uses_a_bounded_prefetch_path_for_many_subjects(django_assert_num_queries):
    """Catches an N+1 lookup while deriving every continuity result."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    for index in range(5):
        enrollment = StudentSubjectFactory(
            student_profile=profile,
            subject=SubjectFactory(
                code=f'PRG{index}10', continuity_code=f'PRG{index}', grade=10
            ),
        )
        CBCGradeFactory(student_subject=enrollment, level='ME1')

    client = APIClient()
    client.force_authenticate(profile.user)
    with django_assert_num_queries(4):
        response = client.get(PROGRESS_URL)

    assert response.status_code == 200
    assert len(response.data['data']['subjects']) == 5


def test_overall_uses_explicit_severity_precedence_not_subject_order_or_averaging():
    """Catches deriving an overall result from ordinal math rather than severity order."""
    result = derive_continuity_progress('ONE', 'One', [evidence(1, 'EE1', 8)])
    support = derive_continuity_progress('TWO', 'Two', [evidence(2, 'BE1', 2)])
    from students.progress import derive_overall_progress

    overall = derive_overall_progress([result, support])

    assert overall == {
        'status': 'support',
        'label': 'Support',
        'subject_continuity_codes': ['TWO'],
    }
