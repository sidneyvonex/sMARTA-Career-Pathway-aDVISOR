import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from tests.factories import (
    AssessmentFrameworkFactory,
    CBCGradeFactory,
    PerformanceLevelDefinitionFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    SchoolAdminFactory,
    SchoolFactory,
    SubjectFactory,
    VerifiedUserFactory,
)


def test_assessment_framework_rejects_unknown_status():
    """Catches accepting framework states outside draft/active/retired."""
    try:
        framework_model = apps.get_model('students', 'AssessmentFramework')
    except LookupError:
        pytest.fail('AssessmentFramework must version academic evidence.')

    framework = framework_model(
        code='CBC-SENIOR-SCHOOL',
        version='pilot-2026',
        title='Senior School CBC Pilot Assessment Framework',
        scope='senior_school',
        source_url='https://kicd.ac.ke/curriculum-reform/',
        effective_date='2026-01-01',
        status='published',
    )

    with pytest.raises(ValidationError, match='not a valid choice'):
        framework.full_clean(validate_unique=False, validate_constraints=False)


def test_performance_level_allows_unavailable_official_values():
    """Catches forcing invented official score ranges or points."""
    try:
        level_model = apps.get_model('students', 'PerformanceLevelDefinition')
    except LookupError:
        pytest.fail('PerformanceLevelDefinition must version level meaning.')

    level = level_model(
        code='EE1',
        label='Exceeding Expectation - Level 1',
        description='Exceeding Expectation - Level 1',
        rank=8,
        official_min_score=None,
        official_max_score=None,
        official_points=None,
    )

    level.full_clean(
        exclude={'framework'},
        validate_unique=False,
        validate_constraints=False,
    )
    assert level.official_min_score is None
    assert level.official_max_score is None
    assert level.official_points is None


@pytest.mark.django_db
def test_framework_code_and_version_are_unique_together():
    """Catches storing two definitions for one versioned framework identity."""
    first = AssessmentFrameworkFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        AssessmentFrameworkFactory(code=first.code, version=first.version)


@pytest.mark.django_db
def test_only_one_active_framework_exists_per_scope():
    """Catches ambiguous active evidence interpretation within one scope."""
    first = AssessmentFrameworkFactory(status='active')

    with pytest.raises(IntegrityError), transaction.atomic():
        AssessmentFrameworkFactory(scope=first.scope, status='active')

    AssessmentFrameworkFactory(scope='experimental_scope', status='active')


@pytest.mark.django_db
def test_level_definitions_are_returned_in_descending_rank_order():
    """Catches reversing the directional level order used by later progress rules."""
    framework = AssessmentFrameworkFactory()
    PerformanceLevelDefinitionFactory(framework=framework, code='BE2', rank=1)
    PerformanceLevelDefinitionFactory(framework=framework, code='ME2', rank=5)
    PerformanceLevelDefinitionFactory(framework=framework, code='EE1', rank=8)

    assert list(framework.level_definitions.values_list('code', flat=True)) == [
        'EE1',
        'ME2',
        'BE2',
    ]


@pytest.mark.django_db
@pytest.mark.parametrize('duplicate_field', ['code', 'rank'])
def test_level_code_and_rank_are_unique_within_a_framework(duplicate_field):
    """Catches ambiguous codes or directional ranks within one framework."""
    framework = AssessmentFrameworkFactory()
    original = PerformanceLevelDefinitionFactory(
        framework=framework,
        code='ME1',
        rank=6,
    )
    values = {'framework': framework, 'code': 'ME2', 'rank': 5}
    values[duplicate_field] = getattr(original, duplicate_field)

    with pytest.raises(IntegrityError), transaction.atomic():
        PerformanceLevelDefinitionFactory(**values)


@pytest.mark.django_db
def test_grade_api_rejects_negative_raw_score_with_standard_envelope():
    """Catches accepting impossible negative raw assessment evidence."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'))
    enrollment = StudentSubjectFactory(student_profile=profile)
    client = APIClient()
    client.force_authenticate(profile.user)

    response = client.post(
        f'/api/v1/students/my-subjects/{enrollment.id}/grades/',
        {
            'term': 1,
            'year': 2026,
            'level': 'ME1',
            'raw_score': '-0.01',
        },
        format='json',
    )

    assert response.status_code == 400
    assert response.data['data'] is None
    assert response.data['error'] is True
    assert 'raw_score' in response.data['message']


@pytest.mark.django_db
def test_grade_api_snapshots_active_framework_and_subject_academic_grade():
    """Catches trusting forged provenance instead of the active framework and subject."""
    active_framework = apps.get_model('students', 'AssessmentFramework').objects.get(
        code='CBC-SENIOR-SCHOOL',
        version='pilot-2026',
    )
    forged_framework = AssessmentFrameworkFactory(status='draft')
    profile = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        grade=10,
    )
    enrollment = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(grade=10),
    )
    client = APIClient()
    client.force_authenticate(profile.user)

    response = client.post(
        f'/api/v1/students/my-subjects/{enrollment.id}/grades/',
        {
            'term': 1,
            'year': 2026,
            'level': 'ME1',
            'raw_score': '1450.75',
            'framework': forged_framework.id,
            'academic_grade': 12,
        },
        format='json',
    )

    assert response.status_code == 201
    assert {'framework', 'academic_grade', 'raw_score'} <= set(response.data['data'])
    assert response.data['data']['framework'] == active_framework.id
    assert response.data['data']['academic_grade'] == enrollment.subject.grade
    assert response.data['data']['raw_score'] == '1450.75'


@pytest.mark.django_db
@pytest.mark.parametrize('academic_grade', [9, 10, 11, 12])
def test_grade_model_supports_academic_grades_nine_through_twelve(academic_grade):
    """Catches rejecting evidence from a supported academic grade."""
    grade = CBCGradeFactory(academic_grade=academic_grade)

    grade.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize('academic_grade', [8, 13])
def test_grade_model_rejects_academic_grades_outside_nine_through_twelve(
    academic_grade,
):
    """Catches evidence being assigned outside the supported model range."""
    grade = CBCGradeFactory(academic_grade=academic_grade)

    with pytest.raises(ValidationError, match='academic_grade'):
        grade.full_clean()


@pytest.mark.django_db
def test_school_verification_snapshots_the_verifying_school():
    """Catches recording only a mutable staff account without school provenance."""
    school = SchoolFactory()
    admin = SchoolAdminFactory(school=school)
    profile = StudentProfileFactory(
        school=school,
        mode='school_linked',
        school_membership_status='active',
    )
    grade = CBCGradeFactory(
        student_subject=StudentSubjectFactory(student_profile=profile)
    )
    client = APIClient()
    client.force_authenticate(admin)

    response = client.put(
        f'/api/v1/school-admin/students/{profile.user_id}/grades/'
        f'{grade.id}/verification/',
        {'verified': True},
        format='json',
    )

    assert response.status_code == 200
    assert 'verified_school' in response.data['data']
    grade.refresh_from_db()
    assert grade.verified_school == school
    assert response.data['data']['verified_school'] == school.id


@pytest.mark.django_db
@pytest.mark.parametrize('replacement', ['another_school', 'none'])
def test_verifying_school_is_immutable_once_recorded(replacement):
    """Catches changing or erasing the school provenance of historical evidence."""
    original_school = SchoolFactory()
    grade = CBCGradeFactory(verified_school=original_school)
    grade.verified_school = (
        SchoolFactory() if replacement == 'another_school' else None
    )

    with pytest.raises(ValidationError, match='verified_school'):
        grade.save(update_fields=['verified_school'])


@pytest.mark.django_db
def test_removing_verification_retains_verifying_school_provenance():
    """Catches unverification erasing the school that supplied the evidence."""
    school = SchoolFactory()
    admin = SchoolAdminFactory(school=school)
    profile = StudentProfileFactory(
        school=school,
        mode='school_linked',
        school_membership_status='active',
    )
    grade = CBCGradeFactory(
        student_subject=StudentSubjectFactory(student_profile=profile),
        verified_by=admin,
        verified_at='2026-07-30T10:00:00Z',
        verified_school=school,
    )
    client = APIClient()
    client.force_authenticate(admin)

    response = client.put(
        f'/api/v1/school-admin/students/{profile.user_id}/grades/'
        f'{grade.id}/verification/',
        {'verified': False},
        format='json',
    )

    assert response.status_code == 200
    grade.refresh_from_db()
    assert grade.verified_by is None
    assert grade.verified_at is None
    assert grade.verified_school == school


@pytest.mark.django_db
def test_legacy_model_create_fails_clearly_without_an_active_framework():
    """Catches persisting unversioned evidence when framework setup is missing."""
    framework_model = apps.get_model('students', 'AssessmentFramework')
    framework_model.objects.filter(scope='senior_school').delete()
    enrollment = StudentSubjectFactory(
        student_profile=StudentProfileFactory(grade=10),
        subject=SubjectFactory(grade=10),
    )

    with pytest.raises(ValidationError, match='No active Senior School'):
        framework_model._meta.apps.get_model('students', 'CBCGrade').objects.create(
            student_subject=enrollment,
            term=1,
            year=2026,
            level='ME1',
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('academic_grade', 'framework_code'),
    [(9, 'CBC-GRADE-9-LEGACY'), (10, 'CBC-SENIOR-SCHOOL')],
)
def test_legacy_model_create_derives_grade_appropriate_framework(
    academic_grade,
    framework_code,
):
    """Catches assigning Grade 9 evidence to the Senior School framework."""
    enrollment = StudentSubjectFactory(
        student_profile=StudentProfileFactory(grade=academic_grade),
        subject=SubjectFactory(grade=academic_grade),
    )
    grade_model = apps.get_model('students', 'CBCGrade')

    grade = grade_model.objects.create(
        student_subject=enrollment,
        term=1,
        year=2026,
        level='ME1',
    )

    assert grade.academic_grade == academic_grade
    assert grade.framework.code == framework_code
