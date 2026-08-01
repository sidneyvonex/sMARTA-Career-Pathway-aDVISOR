from datetime import datetime, timezone

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError


pytestmark = pytest.mark.django_db(transaction=True)


def test_longitudinal_subject_backfill_preserves_identity_and_earliest_evidence_year():
    executor = MigrationExecutor(connection)
    old_targets = [
        ('accounts', '0011_school_official_identity'),
        ('students', '0009_version_assessment_evidence'),
    ]
    executor.migrate(old_targets)
    old_apps = executor.loader.project_state(old_targets).apps

    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Subject = old_apps.get_model('students', 'Subject')
    StudentSubject = old_apps.get_model('students', 'StudentSubject')
    CBCGrade = old_apps.get_model('students', 'CBCGrade')
    AssessmentFramework = old_apps.get_model('students', 'AssessmentFramework')

    learner = User.objects.create(
        email='longitudinal-migration@example.com',
        first_name='Longitudinal',
        last_name='Learner',
        role='student',
        county='kiambu',
        is_email_verified=True,
    )
    profile = StudentProfile.objects.create(
        user=learner,
        mode='self_guided',
        school_membership_status='not_applicable',
        grade=10,
    )
    english_nine = Subject.objects.get(code='ENG9')
    english_ten = Subject.objects.get(code='ENG10')
    evidenced = StudentSubject.objects.create(
        student_profile=profile,
        subject=english_nine,
    )
    no_evidence = StudentSubject.objects.create(
        student_profile=profile,
        subject=english_ten,
    )
    StudentSubject.objects.filter(pk=no_evidence.pk).update(
        created_at=datetime(2024, 2, 3, tzinfo=timezone.utc)
    )
    junior_framework = AssessmentFramework.objects.get(scope='junior_school', status='active')
    CBCGrade.objects.create(
        student_subject=evidenced,
        framework=junior_framework,
        academic_grade=9,
        term=2,
        year=2025,
        level='ME2',
    )
    CBCGrade.objects.create(
        student_subject=evidenced,
        framework=junior_framework,
        academic_grade=9,
        term=1,
        year=2024,
        level='AE1',
    )

    executor = MigrationExecutor(connection)
    new_targets = [
        ('accounts', '0012_expand_student_profile_grades'),
        ('students', '0010_preserve_longitudinal_subject_history'),
    ]
    executor.migrate(new_targets)
    new_apps = executor.loader.project_state(new_targets).apps

    MigratedSubject = new_apps.get_model('students', 'Subject')
    MigratedEnrollment = new_apps.get_model('students', 'StudentSubject')
    migrated_evidenced = MigratedEnrollment.objects.get(pk=evidenced.pk)
    migrated_without_evidence = MigratedEnrollment.objects.get(pk=no_evidence.pk)

    assert MigratedSubject.objects.get(code='ENG9').continuity_code == 'ENG'
    assert MigratedSubject.objects.get(code='ENG10').continuity_code == 'ENG'
    assert (
        migrated_evidenced.continuity_code,
        migrated_evidenced.academic_grade,
        migrated_evidenced.academic_year,
        migrated_evidenced.is_active,
        migrated_evidenced.ended_at,
    ) == ('ENG', 9, 2024, True, None)
    assert migrated_without_evidence.academic_year == 2024


def test_active_identity_migration_is_mysql_safe_and_blocks_incompatible_reverse():
    executor = MigrationExecutor(connection)
    old_targets = [
        ('accounts', '0012_expand_student_profile_grades'),
        ('students', '0010_preserve_longitudinal_subject_history'),
    ]
    executor.migrate(old_targets)
    old_apps = executor.loader.project_state(old_targets).apps

    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Subject = old_apps.get_model('students', 'Subject')
    StudentSubject = old_apps.get_model('students', 'StudentSubject')

    learner = User.objects.create(
        email='active-identity-migration@example.com',
        first_name='Active',
        last_name='Identity',
        role='student',
        county='kiambu',
        is_email_verified=True,
    )
    profile = StudentProfile.objects.create(
        user=learner,
        mode='self_guided',
        school_membership_status='not_applicable',
        grade=9,
    )
    subject = Subject.objects.create(
        name='Migration English',
        code='ENG9-IDENTITY',
        continuity_code='ENG',
        grade=9,
        category='Core',
        is_active=True,
    )
    archived = StudentSubject.objects.create(
        student_profile=profile,
        subject=subject,
        continuity_code='ENG',
        academic_grade=9,
        academic_year=2025,
        is_active=False,
        ended_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    active = StudentSubject.objects.create(
        student_profile=profile,
        subject=subject,
        continuity_code='ENG',
        academic_grade=9,
        academic_year=2026,
        is_active=True,
        ended_at=None,
    )

    executor = MigrationExecutor(connection)
    new_targets = [
        ('accounts', '0012_expand_student_profile_grades'),
        ('students', '0011_enforce_active_identity_and_protect_history'),
    ]
    executor.migrate(new_targets)
    new_state = executor.loader.project_state(new_targets)
    new_apps = new_state.apps
    MigratedEnrollment = new_apps.get_model('students', 'StudentSubject')
    active_constraint = next(
        constraint
        for constraint in new_state.models['students', 'studentsubject'].options[
            'constraints'
        ]
        if constraint.name == 'students_active_identity_uniq'
    )

    assert active_constraint.condition is None
    assert active_constraint.fields == ('student_profile', 'active_identity')
    assert MigratedEnrollment._meta.get_field('active_identity').null is True
    assert MigratedEnrollment.objects.get(pk=archived.pk).active_identity is None
    assert MigratedEnrollment.objects.get(pk=active.pk).active_identity == 'ENG:9'

    executor = MigrationExecutor(connection)
    with pytest.raises(
        IrreversibleError,
        match='archived enrollment history',
    ):
        executor.migrate(old_targets)

    assert MigratedEnrollment.objects.filter(pk__in=[archived.pk, active.pk]).count() == 2
