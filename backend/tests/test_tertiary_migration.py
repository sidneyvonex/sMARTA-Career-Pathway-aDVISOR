import sqlite3

import pytest
from django.db import OperationalError, connection
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)

TERTIARY_MODEL_NAMES = (
    'LearnerEducationGoal',
    'ProgrammeSubjectReference',
    'HistoricalAdmissionReference',
    'Programme',
    'Institution',
)


def _capture_tertiary_baseline_pks():
    """Capture the leaf-schema rows that this migration test must preserve."""
    executor = MigrationExecutor(connection)
    apps = executor.loader.project_state(executor.loader.graph.leaf_nodes()).apps
    return {
        model_name: set(
            apps.get_model('tertiary', model_name).objects.values_list('pk', flat=True)
        )
        for model_name in TERTIARY_MODEL_NAMES
    }


def _delete_tertiary_rows_created_after(baseline_pks):
    """Delete only rows added by this test, using the currently applied model state."""
    executor = MigrationExecutor(connection)
    apps = executor.loader.project_state(
        list(executor.loader.applied_migrations)
    ).apps
    for model_name in TERTIARY_MODEL_NAMES:
        Model = apps.get_model('tertiary', model_name)
        current_pks = set(Model.objects.values_list('pk', flat=True))
        created_pks = current_pks - baseline_pks[model_name]
        if created_pks:
            Model.objects.filter(pk__in=created_pks).delete()


@pytest.fixture(autouse=True)
def restore_complete_migration_graph():
    """Isolate added tertiary rows and restore every test to the graph leaf.

    Task 7 migration tests create fresh rows only; they never update baseline
    catalogue rows, so a primary-key snapshot is sufficient to preserve the
    baseline state while migrations run backwards.
    """
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())
    baseline_pks = _capture_tertiary_baseline_pks()
    try:
        yield
    finally:
        _delete_tertiary_rows_created_after(baseline_pks)
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())


def _old_models():
    executor = MigrationExecutor(connection)
    old_targets = [('tertiary', '0002_programmesubjectreference_tertiary_subj_mapping_kind_ck')]
    executor.migrate(old_targets)
    return executor.loader.project_state(old_targets).apps


def test_migration_cleanup_preserves_leaf_baseline_rows_after_rollback():
    """Catches cleanup that erases catalogue data present before a migration test."""
    executor = MigrationExecutor(connection)
    leaf_targets = executor.loader.graph.leaf_nodes()
    executor.migrate(leaf_targets)
    apps = executor.loader.project_state(leaf_targets).apps
    User = apps.get_model('accounts', 'User')
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    Institution = apps.get_model('tertiary', 'Institution')
    Programme = apps.get_model('tertiary', 'Programme')
    SubjectReference = apps.get_model('tertiary', 'ProgrammeSubjectReference')
    HistoricalReference = apps.get_model('tertiary', 'HistoricalAdmissionReference')
    Goal = apps.get_model('tertiary', 'LearnerEducationGoal')
    user = User.objects.create(
        email='baseline-cleanup@example.com', first_name='Baseline', last_name='Keeper',
        role='student', county='kiambu', is_email_verified=True,
    )
    learner = StudentProfile.objects.create(
        user=user, mode='self_guided', school_membership_status='not_applicable', grade=10,
    )
    common = {
        'source_scope': 'baseline-source', 'source_url': 'https://example.ac.ke/baseline',
        'education_framework': 'KCSE', 'admission_cycle': '2025/2026',
        'effective_date': '2025-03-01', 'verification_status': 'historical',
    }
    institution = Institution.objects.create(
        external_key='BASELINE-INST', name='Baseline University',
        institution_type='university', county='Nairobi', website_url='', **common,
    )
    programme = Programme.objects.create(
        institution=institution, external_key='BASELINE-PROG', code='BASE',
        name='Baseline Programme', description='', **common,
    )
    subject_reference = SubjectReference.objects.create(
        programme=programme, external_key='BASELINE-SUBJ', subject_code='ENG',
        subject_name='English', mapping_kind='historical_requirement', notes='', **common,
    )
    historical_reference = HistoricalReference.objects.create(
        programme=programme, external_key='BASELINE-HIST',
        requirement_summary='Grade C', **common,
    )
    goal = Goal.objects.create(
        learner=learner, institution=institution, programme=programme,
        kind='primary', priority=1, created_by=user,
    )
    baseline_pks = _capture_tertiary_baseline_pks()

    old_apps = _old_models()
    OldInstitution = old_apps.get_model('tertiary', 'Institution')
    OldProgramme = old_apps.get_model('tertiary', 'Programme')
    OldSubjectReference = old_apps.get_model('tertiary', 'ProgrammeSubjectReference')
    OldHistoricalReference = old_apps.get_model('tertiary', 'HistoricalAdmissionReference')
    OldGoal = old_apps.get_model('tertiary', 'LearnerEducationGoal')
    created_institution = OldInstitution.objects.create(
        external_key='CREATED-INST', name='Created University',
        institution_type='university', county='Nairobi', website_url='', **common,
    )
    created_programme = OldProgramme.objects.create(
        institution=created_institution, external_key='CREATED-PROG', code='CREATED',
        name='Created Programme', description='', **common,
    )
    created_subject_reference = OldSubjectReference.objects.create(
        programme=created_programme, external_key='CREATED-SUBJ', subject_code='MAT',
        subject_name='Mathematics', mapping_kind='historical_requirement', notes='', **common,
    )
    created_historical_reference = OldHistoricalReference.objects.create(
        programme=created_programme, external_key='CREATED-HIST',
        requirement_summary='Grade B', **common,
    )
    created_goal = OldGoal.objects.create(
        learner_id=learner.pk, institution=created_institution,
        programme=created_programme, kind='alternative', priority=2, created_by_id=user.pk,
    )

    _delete_tertiary_rows_created_after(baseline_pks)
    MigrationExecutor(connection).migrate(leaf_targets)

    restored_apps = MigrationExecutor(connection).loader.project_state(leaf_targets).apps
    for model_name, baseline_pk, created_pk in (
        ('Institution', institution.pk, created_institution.pk),
        ('Programme', programme.pk, created_programme.pk),
        ('ProgrammeSubjectReference', subject_reference.pk, created_subject_reference.pk),
        ('HistoricalAdmissionReference', historical_reference.pk, created_historical_reference.pk),
        ('LearnerEducationGoal', goal.pk, created_goal.pk),
    ):
        Model = restored_apps.get_model('tertiary', model_name)
        assert Model.objects.filter(pk=baseline_pk).exists()
        assert not Model.objects.filter(pk=created_pk).exists()


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


def test_0003_constraints_fit_a_conservative_sqlite_expression_depth():
    """Catches provenance checks that overflow SQLite's parser in CI."""
    _old_models()
    raw_connection = connection.connection
    previous_limit = raw_connection.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 30)
    try:
        MigrationExecutor(connection).migrate([
            ('tertiary', '0003_enforce_catalogue_integrity'),
        ])
    finally:
        raw_connection.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, previous_limit)


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


@pytest.mark.parametrize(
    ('field', 'whitespace'),
    [
        ('source_scope', '\xa0'), ('external_key', '\xa0'),
        ('source_url', '\xa0'), ('education_framework', '\xa0'),
        ('admission_cycle', '\xa0'),
        ('source_scope', '\x85'), ('source_scope', '\u1680'),
        ('source_scope', '\u2000'), ('source_scope', '\u2007'),
        ('source_scope', '\u2028'), ('source_scope', '\u202f'),
        ('source_scope', '\u205f'), ('source_scope', '\u3000'),
    ],
    ids=[
        'scope-nbsp', 'key-nbsp', 'url-nbsp', 'framework-nbsp', 'cycle-nbsp',
        'scope-next-line', 'scope-ogham-space', 'scope-en-quad',
        'scope-figure-space', 'scope-line-separator', 'scope-narrow-nbsp',
        'scope-medium-mathematical-space', 'scope-ideographic-space',
    ],
)
def test_0003_rejects_whitespace_provenance_before_schema_changes(field, whitespace):
    """Catches preflight accepting blank provenance or running after additive DDL."""
    old_apps = _old_models()
    Institution = old_apps.get_model('tertiary', 'Institution')
    provenance = {
        'source_scope': 'migration-source', 'external_key': 'MIG-BLANK',
        'source_url': 'https://example.ac.ke/source', 'education_framework': 'KCSE',
        'admission_cycle': '2025/2026',
    }
    provenance[field] = whitespace
    institution = Institution.objects.create(
        **provenance, effective_date='2025-03-01', verification_status='historical',
        name='Blank Source University',
        institution_type='university', county='Nairobi', website_url='',
    )

    executor = MigrationExecutor(connection)
    with pytest.raises(
        RuntimeError, match=rf'provenance.*Institution {institution.pk}'
    ):
        executor.migrate([('tertiary', '0003_enforce_catalogue_integrity')])

    with pytest.raises(OperationalError), connection.cursor() as cursor:
        cursor.execute(
            'SELECT choice_identity FROM tertiary_learnereducationgoal LIMIT 1'
        )


def test_0003_rejects_existing_goal_programme_institution_mismatch():
    """Catches migration preserving an education goal linked across institutions."""
    old_apps = _old_models()
    User = old_apps.get_model('accounts', 'User')
    StudentProfile = old_apps.get_model('accounts', 'StudentProfile')
    Institution = old_apps.get_model('tertiary', 'Institution')
    Programme = old_apps.get_model('tertiary', 'Programme')
    Goal = old_apps.get_model('tertiary', 'LearnerEducationGoal')
    user = User.objects.create(
        email='goal-mismatch@example.com', first_name='Goal', last_name='Mismatch',
        role='student', county='kiambu', is_email_verified=True,
    )
    learner = StudentProfile.objects.create(
        user=user, mode='self_guided',
        school_membership_status='not_applicable', grade=10,
    )
    common = {
        'source_scope': 'migration-source',
        'source_url': 'https://example.ac.ke/source',
        'education_framework': 'KCSE', 'admission_cycle': '2025/2026',
        'effective_date': '2025-03-01', 'verification_status': 'historical',
        'institution_type': 'university', 'county': 'Nairobi', 'website_url': '',
    }
    selected = Institution.objects.create(
        external_key='SELECTED', name='Selected University', **common,
    )
    programme_parent = Institution.objects.create(
        external_key='PROGRAMME-PARENT', name='Programme Parent', **common,
    )
    programme = Programme.objects.create(
        institution=programme_parent, source_scope='migration-source',
        external_key='MISMATCHED-PROGRAMME',
        source_url='https://example.ac.ke/source', education_framework='KCSE',
        admission_cycle='2025/2026', effective_date='2025-03-01',
        verification_status='historical', code='MIS', name='Mismatch',
        description='',
    )
    goal = Goal.objects.create(
        learner=learner, institution=selected, programme=programme,
        kind='primary', priority=1, created_by=user,
    )

    executor = MigrationExecutor(connection)
    detail = (
        rf'goal {goal.pk}.*programme {programme.pk}.*institution '
        rf'{programme_parent.pk}.*selected institution {selected.pk}'
    )
    with pytest.raises(RuntimeError, match=detail):
        executor.migrate([('tertiary', '0003_enforce_catalogue_integrity')])

    with pytest.raises(OperationalError), connection.cursor() as cursor:
        cursor.execute(
            'SELECT choice_identity FROM tertiary_learnereducationgoal LIMIT 1'
        )
