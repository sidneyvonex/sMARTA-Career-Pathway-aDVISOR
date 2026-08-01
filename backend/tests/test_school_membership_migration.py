import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)


def test_membership_backfill_preserves_profile_state_and_academic_evidence():
    """Catches a transfer rollout dropping legacy links or grade history."""
    executor = MigrationExecutor(connection)
    old_targets = [
        ('accounts', '0012_expand_student_profile_grades'),
        ('students', '0011_enforce_active_identity_and_protect_history'),
    ]
    executor.migrate(old_targets)
    old_apps = executor.loader.project_state(old_targets).apps

    School = old_apps.get_model('accounts', 'School')
    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Subject = old_apps.get_model('students', 'Subject')
    StudentSubject = old_apps.get_model('students', 'StudentSubject')
    CBCGrade = old_apps.get_model('students', 'CBCGrade')
    Framework = old_apps.get_model('students', 'AssessmentFramework')

    school = School.objects.create(
        name='Legacy Membership School',
        county='kiambu',
        school_code='LEGACY-MEMBER',
    )
    profiles = {}
    for index, membership_status in enumerate(('active', 'pending', 'rejected')):
        user = User.objects.create(
            email=f'legacy-membership-{index}@example.com',
            first_name='Legacy',
            last_name=str(index),
            role='student',
            county='kiambu',
            is_email_verified=True,
        )
        profiles[membership_status] = StudentProfile.objects.create(
            user=user,
            mode='school_linked',
            school=school,
            school_membership_status=membership_status,
            grade=10,
        )

    subject = Subject.objects.create(
        name='Legacy Membership Evidence',
        code='MEM10',
        continuity_code='MEM',
        grade=10,
        category='Core',
    )
    enrollment = StudentSubject.objects.create(
        student_profile=profiles['active'],
        subject=subject,
        continuity_code='MEM',
        academic_grade=10,
        academic_year=2026,
        active_identity='MEM:10',
        is_active=True,
    )
    framework = Framework.objects.get(scope='senior_school', status='active')
    grade = CBCGrade.objects.create(
        student_subject=enrollment,
        framework=framework,
        academic_grade=10,
        term=1,
        year=2026,
        level='ME1',
    )

    executor = MigrationExecutor(connection)
    new_targets = [
        ('accounts', '0013_studentschoolmembership'),
        ('students', '0011_enforce_active_identity_and_protect_history'),
    ]
    executor.migrate(new_targets)
    new_state = executor.loader.project_state(new_targets)
    new_apps = new_state.apps
    Membership = new_apps.get_model('accounts', 'StudentSchoolMembership')
    MigratedGrade = new_apps.get_model('students', 'CBCGrade')

    rows = {
        row.status: row
        for row in Membership.objects.order_by('status')
    }
    assert set(rows) == {'active', 'pending', 'rejected'}
    assert rows['active'].active_identity_key == profiles['active'].pk
    assert rows['active'].requested_at == profiles['active'].created_at
    assert rows['active'].started_at == profiles['active'].created_at
    assert rows['pending'].pending_identity_key == profiles['pending'].pk
    assert rows['pending'].requested_at == profiles['pending'].created_at
    assert rows['rejected'].active_identity_key is None
    assert rows['rejected'].pending_identity_key is None
    assert MigratedGrade.objects.filter(pk=grade.pk, level='ME1').exists()

    constraints = {
        item.name: item
        for item in new_state.models[
            'accounts', 'studentschoolmembership'
        ].options['constraints']
    }
    assert constraints['accounts_membership_active_uniq'].condition is None
    assert constraints['accounts_membership_pending_uniq'].condition is None
