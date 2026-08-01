import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)


def test_0013_backfills_only_factual_creation_data_and_marks_legacy_achievement():
    """Catches migration-time fabrication of a confirming actor or evidence."""
    executor = MigrationExecutor(connection)
    old_targets = [
        ('accounts', '0014_enforce_membership_lifecycle_timestamps'),
        ('students', '0012_academic_goals'),
    ]
    executor.migrate(old_targets)
    old_apps = executor.loader.project_state(old_targets).apps

    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Subject = old_apps.get_model('students', 'Subject')
    StudentSubject = old_apps.get_model('students', 'StudentSubject')
    CBCGrade = old_apps.get_model('students', 'CBCGrade')
    AssessmentFramework = old_apps.get_model('students', 'AssessmentFramework')
    PerformanceLevelDefinition = old_apps.get_model(
        'students', 'PerformanceLevelDefinition'
    )
    AcademicGoal = old_apps.get_model('students', 'AcademicGoal')

    learner = User.objects.create(
        email='goal-migration@example.com',
        first_name='Goal',
        last_name='Migration',
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
    subject = Subject.objects.filter(grade=10).first()
    enrollment = StudentSubject.objects.create(
        student_profile=profile,
        subject=subject,
        continuity_code=subject.continuity_code,
        academic_grade=10,
        academic_year=2026,
        active_identity=f'{subject.continuity_code}:10',
        is_active=True,
    )
    framework = AssessmentFramework.objects.get(
        scope='senior_school',
        status='active',
    )
    current_level = PerformanceLevelDefinition.objects.get(
        framework=framework,
        code='ME2',
    )
    target_level = PerformanceLevelDefinition.objects.get(
        framework=framework,
        code='ME1',
    )
    evidence = CBCGrade.objects.create(
        student_subject=enrollment,
        framework=framework,
        academic_grade=10,
        term=1,
        year=2026,
        level='ME2',
        source='learner',
    )
    legacy = AcademicGoal.objects.create(
        learner=profile,
        continuity_code=subject.continuity_code,
        active_identity=None,
        current_evidence=evidence,
        current_level_definition=current_level,
        target_level_definition=target_level,
        current_level_code='ME2',
        current_level_rank=5,
        current_framework_code=framework.code,
        current_framework_version=framework.version,
        target_level_code='ME1',
        target_level_rank=6,
        target_framework_code=framework.code,
        target_framework_version=framework.version,
        target_term=3,
        target_year=2026,
        target_academic_grade=10,
        action_plan='Legacy goal created before lifecycle hardening.',
        status='achieved',
        created_by=learner,
        achieved_at=None,
    )
    active = AcademicGoal.objects.create(
        learner=profile,
        continuity_code=subject.continuity_code,
        active_identity=subject.continuity_code,
        current_evidence=evidence,
        current_level_definition=current_level,
        target_level_definition=target_level,
        current_level_code='ME2',
        current_level_rank=5,
        current_framework_code=framework.code,
        current_framework_version=framework.version,
        target_level_code='ME1',
        target_level_rank=6,
        target_framework_code=framework.code,
        target_framework_version=framework.version,
        target_term=3,
        target_year=2026,
        target_academic_grade=10,
        action_plan='Active goal created before lifecycle hardening.',
        status='active',
        created_by=learner,
    )

    try:
        executor = MigrationExecutor(connection)
        new_targets = [
            ('accounts', '0014_enforce_membership_lifecycle_timestamps'),
            ('students', '0013_harden_academic_goal_lifecycle'),
        ]
        executor.migrate(new_targets)
        new_apps = executor.loader.project_state(new_targets).apps
        MigratedGoal = new_apps.get_model('students', 'AcademicGoal')
        migrated = MigratedGoal.objects.get(pk=legacy.pk)

        assert migrated.creation_evidence_snapshot['evidence_id'] == evidence.pk
        assert migrated.creation_evidence_snapshot['level'] == {
            'code': 'ME2',
            'rank': 5,
        }
        assert (
            migrated.creation_evidence_snapshot['snapshot_provenance']
            == 'migration_0013_best_available'
        )
        assert migrated.legacy_lifecycle_unverifiable is True
        assert migrated.confirmed_by_id is None
        assert migrated.achievement_evidence_snapshot is None
        assert migrated.achieved_at is None

        migrated_active = MigratedGoal.objects.get(pk=active.pk)
        assert migrated_active.legacy_lifecycle_unverifiable is False
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                MigratedGoal.objects.filter(pk=active.pk).update(
                    status='achieved',
                    active_identity=None,
                )
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
