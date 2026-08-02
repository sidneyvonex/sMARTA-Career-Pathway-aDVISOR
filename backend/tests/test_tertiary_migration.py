import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)


def _old_models():
    executor = MigrationExecutor(connection)
    old_targets = [('tertiary', '0002_programmesubjectreference_tertiary_subj_mapping_kind_ck')]
    executor.migrate(old_targets)
    return executor.loader.project_state(old_targets).apps


def _create_old_goal_rows(apps, *, duplicate=False):
    User = apps.get_model('accounts', 'User')
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    Institution = apps.get_model('tertiary', 'Institution')
    LearnerEducationGoal = apps.get_model('tertiary', 'LearnerEducationGoal')

    user = User.objects.create(
        email='tertiary-migration@example.com', first_name='Migration', last_name='Learner',
        role='student', county='kiambu', is_email_verified=True,
    )
    learner = StudentProfile.objects.create(
        user=user, mode='self_guided', school_membership_status='not_applicable', grade=10,
    )
    institution = Institution.objects.create(
        source_scope='migration-source', external_key='MIG-INST',
        source_url='https://example.ac.ke/source', education_framework='KCSE',
        admission_cycle='2025/2026', effective_date='2025-03-01',
        verification_status='historical', name='Migration University',
        institution_type='university', county='Nairobi', website_url='',
    )
    LearnerEducationGoal.objects.create(
        learner=learner, institution=institution, kind='primary', priority=1,
        created_by=user,
    )
    if duplicate:
        LearnerEducationGoal.objects.create(
            learner=learner, institution=institution, kind='alternative', priority=1,
            created_by=user,
        )
    return learner.pk, institution.pk


def test_0003_backfills_mysql_safe_non_null_choice_identity():
    """Catches nullable, unstable, or programme-insensitive education-choice backfills."""
    old_apps = _old_models()
    learner_id, institution_id = _create_old_goal_rows(old_apps)

    executor = MigrationExecutor(connection)
    new_targets = [('tertiary', '0003_enforce_catalogue_integrity')]
    executor.migrate(new_targets)
    new_apps = executor.loader.project_state(new_targets).apps
    Goal = new_apps.get_model('tertiary', 'LearnerEducationGoal')
    goal = Goal.objects.get(learner_id=learner_id)

    assert goal.choice_identity == f'institution:{institution_id}:programme:none'
    field = Goal._meta.get_field('choice_identity')
    assert field.null is False
    assert field.max_length <= 191


def test_0003_fails_with_actionable_error_when_existing_choices_duplicate():
    """Catches migrations silently discarding or arbitrarily merging duplicate choices."""
    old_apps = _old_models()
    _create_old_goal_rows(old_apps, duplicate=True)

    executor = MigrationExecutor(connection)
    with pytest.raises(RuntimeError, match='duplicate education choices.*learner'):
        executor.migrate([('tertiary', '0003_enforce_catalogue_integrity')])


def test_0003_rejects_existing_cross_release_parent_links():
    """Catches migration preserving catalogue rows that already contradict parents."""
    old_apps = _old_models()
    Institution = old_apps.get_model('tertiary', 'Institution')
    Programme = old_apps.get_model('tertiary', 'Programme')
    institution = Institution.objects.create(
        source_scope='source-a', external_key='INST-A',
        source_url='https://example.ac.ke/source-a', education_framework='KCSE',
        admission_cycle='2025/2026', effective_date='2025-03-01',
        verification_status='historical', name='Migration University',
        institution_type='university', county='Nairobi', website_url='',
    )
    Programme.objects.create(
        institution=institution, source_scope='source-b', external_key='PROG-B',
        source_url='https://example.ac.ke/source-b', education_framework='CBE',
        admission_cycle='2026/2027', effective_date='2026-03-01',
        verification_status='verified', code='BSC-X', name='Contradictory programme',
        description='',
    )

    executor = MigrationExecutor(connection)
    with pytest.raises(RuntimeError, match='parent coherence.*Programme'):
        executor.migrate([('tertiary', '0003_enforce_catalogue_integrity')])
