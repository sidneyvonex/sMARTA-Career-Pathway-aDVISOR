import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


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
    framework, _created = Framework.objects.get_or_create(
        code='CBC-SENIOR-SCHOOL',
        version='pilot-2026',
        defaults={
            'title': 'Senior School CBC Pilot Assessment Framework',
            'scope': 'senior_school',
            'source_url': 'https://kicd.ac.ke/curriculum-reform/',
            'effective_date': '2026-01-01',
            'status': 'active',
        },
    )
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
    assert rows['active'].record_source == 'legacy_backfill'
    assert rows['active'].requested_at is None
    assert rows['active'].started_at is None
    assert rows['pending'].pending_identity_key == profiles['pending'].pk
    assert rows['pending'].record_source == 'legacy_backfill'
    assert rows['pending'].requested_at is None
    assert rows['pending'].started_at is None
    assert rows['rejected'].active_identity_key is None
    assert rows['rejected'].pending_identity_key is None
    assert rows['rejected'].record_source == 'legacy_backfill'
    assert rows['rejected'].requested_at is None
    assert MigratedGrade.objects.filter(pk=grade.pk, level='ME1').exists()

    constraints = {
        item.name: item
        for item in new_state.models[
            'accounts', 'studentschoolmembership'
        ].options['constraints']
    }
    assert constraints['accounts_membership_active_uniq'].condition is None
    assert constraints['accounts_membership_pending_uniq'].condition is None
    assert 'accounts_membership_request_time_ck' in constraints
    assert Membership._meta.get_field('requested_at').null is True


def test_lifecycle_constraint_upgrade_preserves_rows_and_rejects_bad_history():
    """Catches deployed 0013 databases retaining the permissive constraint."""
    old_targets = [
        ('accounts', '0013_studentschoolmembership'),
        ('students', '0011_enforce_active_identity_and_protect_history'),
    ]
    new_targets = [
        ('accounts', '0014_enforce_membership_lifecycle_timestamps'),
        ('students', '0011_enforce_active_identity_and_protect_history'),
    ]
    executor = MigrationExecutor(connection)
    assert new_targets[0] in executor.loader.disk_migrations
    executor.migrate(old_targets)
    old_state = executor.loader.project_state(old_targets)
    old_apps = old_state.apps
    School = old_apps.get_model('accounts', 'School')
    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Membership = old_apps.get_model('accounts', 'StudentSchoolMembership')
    old_constraints = {
        item.name
        for item in old_state.models[
            'accounts', 'studentschoolmembership'
        ].options['constraints']
    }
    assert 'accounts_membership_approval_time_ck' in old_constraints
    assert 'accounts_membership_lifecycle_time_ck' not in old_constraints

    school = School.objects.create(
        name='Membership Upgrade School',
        county='kiambu',
        school_code='MEMBERSHIP-UPGRADE',
    )

    def create_profile(suffix):
        user = User.objects.create(
            email=f'membership-upgrade-{suffix}@example.com',
            first_name='Membership',
            last_name=suffix,
            role='student',
            county='kiambu',
            is_email_verified=True,
        )
        return StudentProfile.objects.create(
            user=user,
            mode='school_linked',
            school=school,
            school_membership_status='active',
            grade=10,
        )

    now = timezone.now()
    invalid_profile = create_profile('invalid')
    invalid = Membership.objects.create(
        student_profile=invalid_profile,
        school=school,
        status='active',
        record_source='learner_request',
        active_identity_key=invalid_profile.pk,
        requested_at=now,
        decided_at=None,
        started_at=None,
        ended_at=None,
    )
    pending_profile = create_profile('pending')
    pending = Membership.objects.create(
        student_profile=pending_profile,
        school=school,
        status='pending',
        record_source='learner_request',
        pending_identity_key=pending_profile.pk,
        requested_at=now,
    )
    legacy_profile = create_profile('legacy')
    legacy = Membership.objects.create(
        student_profile=legacy_profile,
        school=school,
        status='active',
        record_source='legacy_backfill',
        active_identity_key=legacy_profile.pk,
        requested_at=None,
        decided_at=None,
        started_at=None,
        ended_at=None,
    )

    with pytest.raises(
        RuntimeError,
        match='incomplete membership lifecycle provenance',
    ):
        MigrationExecutor(connection).migrate(new_targets)
    assert Membership.objects.filter(pk=invalid.pk).exists()

    # Remove only the synthetic invalid fixture so the successful upgrade path
    # can be exercised. The migration itself must never delete or rewrite it.
    Membership.objects.filter(pk=invalid.pk).delete()
    executor = MigrationExecutor(connection)
    executor.migrate(new_targets)
    new_state = executor.loader.project_state(new_targets)
    NewMembership = new_state.apps.get_model(
        'accounts',
        'StudentSchoolMembership',
    )
    assert NewMembership.objects.filter(pk=pending.pk).exists()
    migrated_legacy = NewMembership.objects.get(pk=legacy.pk)
    assert migrated_legacy.requested_at is None
    assert migrated_legacy.decided_at is None
    assert migrated_legacy.started_at is None

    rejected_profile = create_profile('post-upgrade-invalid')
    with pytest.raises(IntegrityError), transaction.atomic():
        NewMembership.objects.create(
            student_profile_id=rejected_profile.pk,
            school_id=school.pk,
            status='rejected',
            record_source='learner_request',
            requested_at=now,
            decided_at=None,
            started_at=None,
            ended_at=None,
        )
