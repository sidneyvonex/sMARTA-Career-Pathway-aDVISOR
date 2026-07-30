from datetime import date
from types import SimpleNamespace

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from counselors.attention import (
    AttentionSnapshot,
    attention_profiles,
    attention_reasons_for,
    derive_attention_reasons,
)
from tests.factories import (
    CBCGradeFactory,
    CounselorAssignmentFactory,
    CounselorFactory,
    RIASECAssessmentFactory,
    SchoolFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    SubjectFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db


REASON_CASES = [
    (
        'assessment_missing',
        {'assessment_complete': False},
    ),
    (
        'academic_evidence_missing',
        {'academic_evidence_ready': False},
    ),
    (
        'no_saved_combination',
        {'saved_combination_count': 0},
    ),
    (
        'no_plan',
        {'has_plan': False},
    ),
    (
        'learner_requested_review',
        {'learner_requested_review': True},
    ),
    (
        'follow_up_overdue',
        {'follow_up_overdue': True},
    ),
    (
        'combination_unavailable_at_school',
        {'selected_combination_available': False},
    ),
]


@pytest.mark.parametrize(('expected_code', 'override'), REASON_CASES)
def test_each_attention_reason_is_derived_independently(expected_code, override):
    values = {
        'assessment_complete': True,
        'academic_evidence_ready': True,
        'saved_combination_count': 1,
        'has_plan': True,
        'learner_requested_review': False,
        'follow_up_overdue': False,
        'selected_combination_available': True,
    }
    values.update(override)

    reasons = derive_attention_reasons(AttentionSnapshot(**values))

    assert [reason['code'] for reason in reasons] == [expected_code]
    assert reasons[0]['label']
    assert reasons[0]['guidance']


def test_complete_learner_has_no_false_attention_reason():
    reasons = derive_attention_reasons(
        AttentionSnapshot(
            assessment_complete=True,
            academic_evidence_ready=True,
            saved_combination_count=2,
            has_plan=True,
            learner_requested_review=False,
            follow_up_overdue=False,
            selected_combination_available=True,
        )
    )

    assert reasons == []


def test_follow_up_is_overdue_only_when_open_and_before_today():
    profile = SimpleNamespace(
        attention_assessments=[object()],
        attention_subjects=[],
        attention_choices=[object()],
        school_id=None,
    )
    follow_ups = [
        SimpleNamespace(status='completed', follow_up_date=date(2026, 7, 1)),
        SimpleNamespace(status='open', follow_up_date=date(2026, 7, 31)),
    ]

    reasons = attention_reasons_for(
        profile,
        follow_ups=follow_ups,
        today=date(2026, 7, 30),
    )

    assert 'follow_up_overdue' not in [reason['code'] for reason in reasons]

    follow_ups.append(
        SimpleNamespace(status='open', follow_up_date=date(2026, 7, 29))
    )
    reasons = attention_reasons_for(
        profile,
        follow_ups=follow_ups,
        today=date(2026, 7, 30),
    )

    assert 'follow_up_overdue' in [reason['code'] for reason in reasons]


def test_attention_context_query_count_stays_bounded_with_larger_caseload():
    school = SchoolFactory()
    counselor = CounselorFactory(school=school)
    for learner_index in range(6):
        profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            school=school,
            mode='school_linked',
            grade=9,
        )
        CounselorAssignmentFactory(
            counselor=counselor,
            student_profile=profile,
            school=school,
        )
        RIASECAssessmentFactory(student_profile=profile)
        for subject_index in range(3):
            enrollment = StudentSubjectFactory(
                student_profile=profile,
                subject=SubjectFactory(
                    code=f'ATT-{learner_index}-{subject_index}',
                    grade=9,
                ),
            )
            CBCGradeFactory(student_subject=enrollment)

    profiles = StudentProfileFactory._meta.model.objects.filter(
        counselor_assignments__counselor=counselor,
        counselor_assignments__is_active=True,
    )

    with CaptureQueriesContext(connection) as queries:
        results = [
            attention_reasons_for(profile)
            for profile in attention_profiles(profiles)
        ]

    assert len(results) == 6
    assert len(queries) <= 7
