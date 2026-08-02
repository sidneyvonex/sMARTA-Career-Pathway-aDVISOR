import pytest
from django.apps import apps
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Value
from rest_framework.test import APIClient
from students.models import AssessmentFramework, PerformanceLevelDefinition

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


def activate_complete_framework(framework):
    """Create the fixed CBE definition set, then use the public activation path."""
    for code, rank in (
        ('EE1', 8), ('EE2', 7), ('ME1', 6), ('ME2', 5),
        ('AE1', 4), ('AE2', 3), ('BE1', 2), ('BE2', 1),
    ):
        PerformanceLevelDefinitionFactory(
            framework=framework,
            code=code,
            rank=rank,
        )
    framework.activate()
    return framework


def test_grade_admin_makes_all_verification_provenance_read_only():
    """Catches admin edits bypassing the school verification workflow."""
    from students.admin import CBCGradeAdmin

    grade_model = apps.get_model('students', 'CBCGrade')
    grade_admin = CBCGradeAdmin(grade_model, AdminSite())

    assert {'verified_by', 'verified_at', 'verified_school'} <= set(
        grade_admin.get_readonly_fields(request=None)
    )


@pytest.mark.django_db
def test_grade_admin_makes_verified_evidence_view_only_and_non_deletable():
    """Catches admin edits or deletes bypassing verified evidence locks."""
    from students.admin import CBCGradeAdmin

    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
    )
    grade_admin = CBCGradeAdmin(type(grade), AdminSite())

    readonly = set(grade_admin.get_readonly_fields(request=None, obj=grade))

    assert {'level', 'raw_score', 'source', 'term', 'year'} <= readonly
    assert grade_admin.has_delete_permission(request=None, obj=grade) is False


@pytest.mark.django_db
def test_verified_evidence_rejects_instance_identity_edits():
    """Catches direct ORM saves mutating a school-verified evidence row."""
    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
    )
    grade.level = 'EE1'

    with pytest.raises(ValidationError, match='verified evidence'):
        grade.save(update_fields=['level'])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('operation', 'message'),
    [
        ('verification_update', 'bulk persistence'),
        ('verified_delete', 'verified evidence'),
    ],
)
def test_verified_evidence_rejects_queryset_bypasses(operation, message):
    """Catches bulk verification changes and deletion bypassing the service."""
    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
    )

    with pytest.raises(ValidationError, match=message):
        if operation == 'verification_update':
            type(grade).objects.filter(pk=grade.pk).update(verified_at=None)
        else:
            type(grade).objects.filter(pk=grade.pk).delete()

    assert type(grade).objects.filter(pk=grade.pk).exists()


@pytest.mark.django_db
def test_verified_evidence_rejects_base_manager_identity_update():
    """Catches Django's base manager bypassing verified-evidence locks."""
    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
    )

    with pytest.raises(ValidationError, match='bulk persistence'):
        type(grade)._base_manager.filter(pk=grade.pk).update(level='EE1')

    grade.refresh_from_db()
    assert grade.level == 'ME1'


@pytest.mark.django_db
def test_verified_evidence_rejects_base_manager_delete():
    """Catches the generated base manager bypassing verified deletion locks."""
    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
    )

    with pytest.raises(ValidationError, match='verified evidence'):
        type(grade)._base_manager.filter(pk=grade.pk).delete()

    assert type(grade).objects.filter(pk=grade.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize('manager_name', ['objects', '_base_manager'])
@pytest.mark.parametrize('field, value', [
    ('level', 'EE1'),
    ('level_definition_id_snapshot', None),
])
def test_grade_managers_reject_identity_and_snapshot_updates(
    manager_name,
    field,
    value,
):
    """Catches any ordinary manager mutating evidence identity or its snapshot."""
    grade = CBCGradeFactory()
    manager = getattr(type(grade), manager_name)

    with pytest.raises(ValidationError, match='bulk persistence'):
        manager.filter(pk=grade.pk).update(**{field: value})

    grade.refresh_from_db()
    assert grade.level == 'ME1'
    assert grade.level_definition_id_snapshot is not None


@pytest.mark.django_db
@pytest.mark.parametrize('manager_name', ['objects', '_base_manager'])
def test_grade_managers_reject_bulk_deletion(manager_name):
    """Catches unverified history deletion through a default or base queryset."""
    grade = CBCGradeFactory()
    manager = getattr(type(grade), manager_name)

    with pytest.raises(ValidationError, match='bulk deletion'):
        manager.filter(pk=grade.pk).delete()

    assert type(grade).objects.filter(pk=grade.pk).exists()


@pytest.mark.django_db
def test_unverified_evidence_allows_instance_edit():
    """Catches turning the verified-evidence guard into an edit lock."""
    grade = CBCGradeFactory()
    grade.level = 'EE1'
    grade.save(update_fields=['level'])
    grade.refresh_from_db()

    assert grade.level == 'EE1'
    assert grade.level_definition_id_snapshot == PerformanceLevelDefinition.objects.get(
        framework=grade.framework,
        code='EE1',
    ).id


@pytest.mark.django_db
def test_unverified_evidence_allows_instance_delete():
    """Catches turning the verified-evidence guard into a deletion lock."""
    grade = CBCGradeFactory()
    grade_id = grade.id

    grade.delete()
    assert not type(grade).objects.filter(pk=grade_id).exists()


@pytest.mark.django_db
def test_history_snapshot_rewrite_requires_audited_reason_and_is_narrow():
    """Catches raw-manager compatibility rewrites outside the named history path."""
    from students.evidence import rewrite_grade_definition_snapshot_for_history

    grade = CBCGradeFactory()
    original_level = grade.level
    original_framework_id = grade.framework_id

    with pytest.raises(ValidationError, match='audit reason'):
        rewrite_grade_definition_snapshot_for_history(
            grade_id=grade.id,
            definition_id=None,
            audit_reason='  ',
        )

    rewrite_grade_definition_snapshot_for_history(
        grade_id=grade.id,
        definition_id=None,
        audit_reason='Legacy import omitted definition snapshot.',
    )
    grade.refresh_from_db()

    assert grade.level_definition_id_snapshot is None
    assert grade.level == original_level
    assert grade.framework_id == original_framework_id


@pytest.mark.django_db
def test_incomplete_framework_rejects_direct_active_create():
    """Catches direct persistence of an incomplete active framework."""
    incomplete = AssessmentFrameworkFactory.build(
        status=AssessmentFramework.STATUS_ACTIVE,
    )

    with pytest.raises(ValidationError, match='EE1–BE2'):
        AssessmentFramework.objects.create(
            code=incomplete.code,
            version=incomplete.version,
            title=incomplete.title,
            scope=incomplete.scope,
            source_url=incomplete.source_url,
            effective_date=incomplete.effective_date,
            status=incomplete.status,
        )

    assert not AssessmentFramework.objects.filter(code=incomplete.code).exists()


@pytest.mark.django_db
def test_incomplete_framework_rejects_direct_model_activation():
    """Catches an incomplete draft changing status through model save."""
    model_framework = AssessmentFrameworkFactory()
    model_framework.status = AssessmentFramework.STATUS_ACTIVE
    with pytest.raises(ValidationError, match='EE1–BE2'):
        model_framework.save(update_fields=['status'])

    model_framework.refresh_from_db()
    assert model_framework.status == AssessmentFramework.STATUS_DRAFT


@pytest.mark.django_db
def test_incomplete_framework_admin_form_rejects_activation():
    """Catches admin surfacing readiness failures only after form submission."""
    from students.admin import AssessmentFrameworkAdmin

    admin_framework = AssessmentFrameworkFactory()
    framework_admin = AssessmentFrameworkAdmin(
        type(admin_framework),
        AdminSite(),
    )
    form_class = framework_admin.get_form(request=None, obj=admin_framework)
    form = form_class(
        data={
            'code': admin_framework.code,
            'version': admin_framework.version,
            'title': admin_framework.title,
            'scope': admin_framework.scope,
            'source_url': admin_framework.source_url,
            'effective_date': admin_framework.effective_date.isoformat(),
            'status': AssessmentFramework.STATUS_ACTIVE,
        },
        instance=admin_framework,
    )

    assert form.is_valid() is False
    assert 'EE1–BE2' in form.non_field_errors().as_text()


@pytest.mark.django_db
@pytest.mark.parametrize('manager_name', ['objects', '_base_manager'])
def test_framework_managers_reject_bulk_activation(manager_name):
    """Catches queryset and bulk-manager activation bypasses."""
    manager = getattr(AssessmentFramework, manager_name)
    framework = AssessmentFrameworkFactory()

    with pytest.raises(ValidationError, match='bulk activation'):
        manager.filter(pk=framework.pk).update(
            status=AssessmentFramework.STATUS_ACTIVE,
        )

    with pytest.raises(ValidationError, match='bulk activation'):
        manager.filter(pk=framework.pk).update(
            status=Value(AssessmentFramework.STATUS_ACTIVE),
        )

    framework.status = AssessmentFramework.STATUS_ACTIVE
    with pytest.raises(ValidationError, match='bulk activation'):
        manager.bulk_update([framework], fields=['status'])

    with pytest.raises(ValidationError, match='bulk activation'):
        manager.bulk_create([
            AssessmentFrameworkFactory.build(
                status=AssessmentFramework.STATUS_ACTIVE,
            )
        ])

    with pytest.raises(ValidationError, match='bulk activation'):
        manager.bulk_create([
            AssessmentFrameworkFactory.build(
                status=Value(AssessmentFramework.STATUS_ACTIVE),
            )
        ])

    framework.refresh_from_db()
    assert framework.status == AssessmentFramework.STATUS_DRAFT


@pytest.mark.django_db
@pytest.mark.parametrize('manager_name', ['objects', '_base_manager'])
def test_framework_managers_allow_non_activation_bulk_status_updates(manager_name):
    """Catches bulk guards unnecessarily blocking safe draft/retired transitions."""
    manager = getattr(AssessmentFramework, manager_name)
    framework = AssessmentFrameworkFactory()
    framework.status = AssessmentFramework.STATUS_RETIRED

    manager.bulk_update([framework], fields=['status'])

    framework.refresh_from_db()
    assert framework.status == AssessmentFramework.STATUS_RETIRED


@pytest.mark.django_db
def test_complete_framework_activates_through_the_supported_model_path():
    """Catches readiness enforcement blocking a complete, deliberate activation."""
    framework = activate_complete_framework(AssessmentFrameworkFactory())

    framework.refresh_from_db()
    assert framework.status == AssessmentFramework.STATUS_ACTIVE


@pytest.mark.django_db
def test_direct_instance_verification_transition_is_rejected():
    """Catches verification changes outside the guarded transition service."""
    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
    )
    grade.verified_by = None
    grade.verified_at = None

    with pytest.raises(ValidationError, match='transition service'):
        grade.save(update_fields=['verified_by', 'verified_at'])


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
    first = activate_complete_framework(AssessmentFrameworkFactory())

    with pytest.raises(IntegrityError), transaction.atomic():
        activate_complete_framework(AssessmentFrameworkFactory(scope=first.scope))

    activate_complete_framework(AssessmentFrameworkFactory(scope='experimental_scope'))


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
    grade = CBCGradeFactory(
        student_subject=StudentSubjectFactory(
            student_profile=StudentProfileFactory(grade=academic_grade),
            subject=SubjectFactory(grade=academic_grade),
        ),
        academic_grade=academic_grade,
    )

    grade.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize('academic_grade', [8, 13])
def test_grade_model_rejects_academic_grades_outside_nine_through_twelve(
    academic_grade,
):
    """Catches evidence being assigned outside the supported model range."""
    grade = CBCGradeFactory.build(academic_grade=academic_grade)

    with pytest.raises(ValidationError, match='academic_grade'):
        grade.full_clean()


@pytest.mark.django_db
def test_new_verified_grade_requires_verifying_school():
    """Catches creating verification without immutable school provenance."""
    verifier = SchoolAdminFactory()
    grade = CBCGradeFactory.build(
        student_subject=StudentSubjectFactory(),
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
        verified_school=None,
    )

    with pytest.raises(ValidationError, match='verified_school'):
        grade.full_clean()


@pytest.mark.django_db
def test_new_verified_grade_rejects_verifier_school_mismatch():
    """Catches claiming one school while the verifier belongs to another."""
    verifier = SchoolAdminFactory()

    grade = CBCGradeFactory.build(
        student_subject=StudentSubjectFactory(),
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
        verified_school=SchoolFactory(),
    )

    with pytest.raises(ValidationError, match='verified_school'):
        grade.full_clean()


@pytest.mark.django_db
def test_explicit_academic_grade_must_match_enrollment_subject():
    """Catches callers assigning evidence to a different academic grade."""
    enrollment = StudentSubjectFactory(
        student_profile=StudentProfileFactory(grade=10),
        subject=SubjectFactory(grade=10),
    )

    grade = CBCGradeFactory.build(
        student_subject=enrollment,
        academic_grade=11,
    )

    with pytest.raises(ValidationError, match='academic_grade'):
        grade.full_clean()


@pytest.mark.django_db
def test_explicit_framework_scope_must_match_academic_grade():
    """Catches assigning Grade 9 evidence to a Senior School framework."""
    senior_framework = apps.get_model('students', 'AssessmentFramework').objects.get(
        code='CBC-SENIOR-SCHOOL',
        version='pilot-2026',
    )
    enrollment = StudentSubjectFactory(
        student_profile=StudentProfileFactory(grade=9),
        subject=SubjectFactory(grade=9),
    )

    grade = CBCGradeFactory.build(
        student_subject=enrollment,
        academic_grade=9,
        framework=senior_framework,
    )

    with pytest.raises(ValidationError, match='framework'):
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
    verifier = SchoolAdminFactory(school=original_school)
    grade = CBCGradeFactory(
        verified_by=verifier,
        verified_at='2026-07-30T10:00:00Z',
        verified_school=original_school,
    )
    grade.verified_school = (
        SchoolFactory() if replacement == 'another_school' else None
    )

    with pytest.raises(ValidationError, match='verification changes'):
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


@pytest.mark.django_db
def test_grade_rejects_framework_without_selected_level_definition():
    """Catches evidence rows with a null, unusable definition snapshot."""
    framework = AssessmentFrameworkFactory(
        scope='senior_school',
    )
    enrollment = StudentSubjectFactory(
        student_profile=StudentProfileFactory(grade=10),
        subject=SubjectFactory(grade=10),
    )
    with pytest.raises(ValidationError, match='performance level definition'):
        CBCGradeFactory(
            student_subject=enrollment,
            framework=framework,
            level='ME1',
        )


@pytest.mark.django_db
def test_grade_identity_change_rejects_framework_without_matching_definition():
    """Catches an identity update persisting without its required definition snapshot."""
    grade = CBCGradeFactory()
    incomplete_framework = AssessmentFrameworkFactory(scope=grade.framework.scope)
    grade.framework = incomplete_framework

    with pytest.raises(ValidationError, match='performance level definition'):
        grade.save(update_fields=['framework'])
