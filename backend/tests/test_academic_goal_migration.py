from datetime import datetime, timezone
from itertools import product

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)


def test_0013_totally_preserves_every_0012_valid_lifecycle_actor_and_evidence_shape():
    """Catches migration rejection, fabrication, or loss for database-valid 0012 rows."""
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

    users = []
    profiles = []
    evidence_rows = []
    framework, _ = AssessmentFramework.objects.get_or_create(
        code='MIGRATION-TEST-SENIOR',
        version='0012',
        defaults={
            'title': 'Migration test framework',
            'scope': 'migration_test_senior',
            'source_url': 'https://example.com/framework',
            'effective_date': '2026-01-01',
            'status': 'active',
        },
    )
    current_level, _ = PerformanceLevelDefinition.objects.get_or_create(
        framework=framework,
        code='ME2',
        defaults={
            'label': 'Meeting Expectation 2',
            'description': 'Migration fixture',
            'rank': 5,
        },
    )
    target_level, _ = PerformanceLevelDefinition.objects.get_or_create(
        framework=framework,
        code='ME1',
        defaults={
            'label': 'Meeting Expectation 1',
            'description': 'Migration fixture',
            'rank': 6,
        },
    )
    subjects = [
        Subject.objects.create(
            name=f"Migration Subject {index}",
            code=f"MIG{index}10",
            continuity_code=f"MIG{index}",
            grade=10,
            category='migration',
        )
        for index in range(2)
    ]
    for index, subject in enumerate(subjects):
        user = User.objects.create(
            email=f"goal-migration-{index}@example.com",
            first_name='Goal',
            last_name=f"Migration {index}",
            role='student',
            county='kiambu',
            is_email_verified=True,
        )
        profile = StudentProfile.objects.create(
            user=user,
            mode='self_guided',
            school_membership_status='not_applicable',
            grade=10,
        )
        enrollment = StudentSubject.objects.create(
            student_profile=profile,
            subject=subject,
            continuity_code=subject.continuity_code,
            academic_grade=10,
            academic_year=2026,
            active_identity=f"{subject.continuity_code}:10",
            is_active=True,
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
        users.append(user)
        profiles.append(profile)
        evidence_rows.append(evidence)

    achieved_value = datetime(2026, 2, 3, 4, 5, tzinfo=timezone.utc)
    closed_value = datetime(2026, 3, 4, 5, 6, tzinfo=timezone.utc)
    expected = {}
    cases = product(
        ('active', 'achieved', 'closed'),
        (False, True),
        (False, True),
        ('owner', 'other'),
        ('owner', 'other'),
    )
    for index, (
        status,
        has_achieved_at,
        has_closed_at,
        actor_shape,
        evidence_shape,
    ) in enumerate(cases):
        created_by = users[0 if actor_shape == 'owner' else 1]
        evidence = evidence_rows[0 if evidence_shape == 'owner' else 1]
        active_identity = f"MIGRATION-{index}" if status == 'active' else None
        goal = AcademicGoal.objects.create(
            learner=profiles[0],
            continuity_code=f"MIGRATION-{index}",
            active_identity=active_identity,
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
            action_plan='Preserve every factual legacy field.',
            status=status,
            created_by=created_by,
            achieved_at=achieved_value if has_achieved_at else None,
            closed_at=closed_value if has_closed_at else None,
        )
        is_normal = (
            status == 'active' and not has_achieved_at and not has_closed_at
        ) or (status == 'closed' and not has_achieved_at and has_closed_at)
        expected[goal.pk] = {
            'status': status,
            'active_identity': active_identity,
            'achieved_at': achieved_value if has_achieved_at else None,
            'closed_at': closed_value if has_closed_at else None,
            'created_by_id': created_by.pk,
            'current_evidence_id': evidence.pk,
            'legacy': not is_normal,
        }

    try:
        executor = MigrationExecutor(connection)
        new_targets = [
            ('accounts', '0014_enforce_membership_lifecycle_timestamps'),
            ('students', '0013_harden_academic_goal_lifecycle'),
        ]
        executor.migrate(new_targets)
        new_apps = executor.loader.project_state(new_targets).apps
        MigratedGoal = new_apps.get_model('students', 'AcademicGoal')
        MigratedGrade = new_apps.get_model('students', 'CBCGrade')

        assert MigratedGoal.objects.count() == len(expected)
        for goal_id, facts in expected.items():
            migrated = MigratedGoal.objects.get(pk=goal_id)
            assert migrated.status == facts['status']
            assert migrated.active_identity == facts['active_identity']
            assert migrated.achieved_at == facts['achieved_at']
            assert migrated.closed_at == facts['closed_at']
            assert migrated.created_by_id == facts['created_by_id']
            assert migrated.current_evidence_id == facts['current_evidence_id']
            assert (
                MigratedGrade.objects.get(
                    pk=facts['current_evidence_id']
                ).level_definition_id_snapshot
                == current_level.pk
            )
            assert migrated.target_framework_id_snapshot == framework.pk
            assert migrated.legacy_lifecycle_unverifiable is facts['legacy']
            assert migrated.confirmed_by_id is None
            assert migrated.achievement_evidence_snapshot is None
            snapshot = migrated.creation_evidence_snapshot
            assert snapshot['evidence_id'] == facts['current_evidence_id']
            assert snapshot['level'] == {
                'code': 'ME2',
                'rank': 5,
                'definition_id': current_level.pk,
            }
            assert snapshot['framework']['id'] == framework.pk
            assert snapshot['framework']['level_definitions'][str(target_level.pk)] == {
                'code': 'ME1',
                'rank': 6,
            }
            assert snapshot['snapshot_provenance'] == ('migration_0013_best_available')

        normal_active = next(
            MigratedGoal.objects.filter(
                status='active',
                legacy_lifecycle_unverifiable=False,
            ).iterator()
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE students_academicgoal '
                        'SET status = %s, active_identity = NULL WHERE id = %s',
                        ['achieved', normal_active.pk],
                    )
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
