from datetime import datetime, timezone

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)


def test_pilot_framework_seed_and_existing_grade_backfill_preserve_evidence():
    """Catches invented ranges or destructive changes to migrated grade evidence."""
    executor = MigrationExecutor(connection)
    old_targets = [
        ('accounts', '0011_school_official_identity'),
        ('students', '0008_full_catalogue_subjects'),
    ]
    executor.migrate(old_targets)
    old_apps = executor.loader.project_state(
        old_targets
    ).apps

    School = old_apps.get_model('accounts', 'School')
    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Subject = old_apps.get_model('students', 'Subject')
    StudentSubject = old_apps.get_model('students', 'StudentSubject')
    CBCGrade = old_apps.get_model('students', 'CBCGrade')

    school = School.objects.create(name='Migration School', county='kiambu')
    verifier_current_school = School.objects.create(
        name='Verifier Current School',
        county='kiambu',
    )
    verifier = User.objects.create(
        email='migration-admin@example.com',
        first_name='Migration',
        last_name='Admin',
        role='school_admin',
        county='kiambu',
        school=verifier_current_school,
        is_email_verified=True,
    )
    learner = User.objects.create(
        email='migration-learner@example.com',
        first_name='Migration',
        last_name='Learner',
        role='student',
        county='kiambu',
        is_email_verified=True,
    )
    profile = StudentProfile.objects.create(
        user=learner,
        mode='school_linked',
        school=school,
        school_membership_status='active',
        grade=10,
    )
    subject = Subject.objects.create(
        name='Migration Subject',
        code='MIG10',
        grade=10,
        category='Core',
    )
    enrollment = StudentSubject.objects.create(
        student_profile=profile,
        subject=subject,
    )
    verified_at = datetime(2026, 7, 30, 7, 0, tzinfo=timezone.utc)
    verified_grade = CBCGrade.objects.create(
        student_subject=enrollment,
        term=1,
        year=2026,
        level='AE2',
        source='school',
        verified_by=verifier,
        verified_at=verified_at,
    )
    unverified_grade = CBCGrade.objects.create(
        student_subject=enrollment,
        term=2,
        year=2026,
        level='EE1',
        source='learner',
    )
    grade_nine_subject = Subject.objects.create(
        name='Legacy Grade 9 Subject',
        code='MIG9',
        grade=9,
        category='Core',
    )
    grade_nine_enrollment = StudentSubject.objects.create(
        student_profile=profile,
        subject=grade_nine_subject,
    )
    grade_nine_evidence = CBCGrade.objects.create(
        student_subject=grade_nine_enrollment,
        term=1,
        year=2025,
        level='ME1',
        source='learner',
    )

    executor = MigrationExecutor(connection)
    new_targets = [
        ('accounts', '0011_school_official_identity'),
        ('students', '0009_version_assessment_evidence'),
    ]
    executor.migrate(new_targets)
    new_apps = executor.loader.project_state(
        new_targets
    ).apps

    AssessmentFramework = new_apps.get_model('students', 'AssessmentFramework')
    PerformanceLevelDefinition = new_apps.get_model(
        'students', 'PerformanceLevelDefinition'
    )
    MigratedGrade = new_apps.get_model('students', 'CBCGrade')

    frameworks = list(AssessmentFramework.objects.all())
    assert len(frameworks) == 2
    framework = AssessmentFramework.objects.get(code='CBC-SENIOR-SCHOOL')
    assert (
        framework.code,
        framework.version,
        framework.title,
        framework.scope,
        framework.status,
    ) == (
        'CBC-SENIOR-SCHOOL',
        'pilot-2026',
        'Senior School CBC Pilot Assessment Framework',
        'senior_school',
        'active',
    )
    junior_framework = AssessmentFramework.objects.get(code='CBC-GRADE-9-LEGACY')
    assert (
        junior_framework.version,
        junior_framework.title,
        junior_framework.scope,
        junior_framework.status,
    ) == (
        'pilot-2026',
        'Grade 9 CBC Legacy Pilot Assessment Framework',
        'junior_school',
        'active',
    )

    levels = list(
        PerformanceLevelDefinition.objects.filter(framework=framework).values_list(
            'code',
            'rank',
            'official_min_score',
            'official_max_score',
            'official_points',
        )
    )
    assert levels == [
        ('EE1', 8, None, None, None),
        ('EE2', 7, None, None, None),
        ('ME1', 6, None, None, None),
        ('ME2', 5, None, None, None),
        ('AE1', 4, None, None, None),
        ('AE2', 3, None, None, None),
        ('BE1', 2, None, None, None),
        ('BE2', 1, None, None, None),
    ]
    assert list(
        PerformanceLevelDefinition.objects.filter(
            framework=junior_framework
        ).values_list(
            'code',
            'rank',
            'official_min_score',
            'official_max_score',
            'official_points',
        )
    ) == levels

    migrated_verified = MigratedGrade.objects.get(pk=verified_grade.pk)
    assert migrated_verified.level == 'AE2'
    assert migrated_verified.source == 'school'
    assert migrated_verified.verified_by_id == verifier.pk
    assert migrated_verified.verified_at == verified_at
    assert migrated_verified.framework_id == framework.pk
    assert migrated_verified.academic_grade == 10
    assert migrated_verified.raw_score is None
    assert migrated_verified.verified_school_id is None

    migrated_unverified = MigratedGrade.objects.get(pk=unverified_grade.pk)
    assert migrated_unverified.level == 'EE1'
    assert migrated_unverified.verified_by_id is None
    assert migrated_unverified.verified_at is None
    assert migrated_unverified.framework_id == framework.pk
    assert migrated_unverified.academic_grade == 10
    assert migrated_unverified.verified_school_id is None

    migrated_grade_nine = MigratedGrade.objects.get(pk=grade_nine_evidence.pk)
    assert migrated_grade_nine.academic_grade == 9
    assert migrated_grade_nine.framework_id == junior_framework.pk
