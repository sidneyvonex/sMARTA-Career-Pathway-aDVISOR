import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from rest_framework.test import APIClient

from counselors.models import CounselorAssignment
from students.admin import AcademicGoalAdmin
from students.models import AcademicGoal, AssessmentFramework, PerformanceLevelDefinition
from tests.factories import (
    AcademicGoalFactory,
    CBCGradeFactory,
    CounselorAssignmentFactory,
    CounselorFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    SubjectFactory,
    SystemAdminFactory,
    VerifiedUserFactory,
)


GOALS_URL = '/api/v1/students/academic-goals/'


def learner_with_evidence(*, continuity_code='MAT', level='ME2', term=1):
    profile = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        grade=10,
    )
    enrollment = StudentSubjectFactory(
        student_profile=profile,
        subject=SubjectFactory(
            code=f'{continuity_code}10',
            continuity_code=continuity_code,
            grade=10,
        ),
    )
    grade = CBCGradeFactory(
        student_subject=enrollment,
        level=level,
        term=term,
        year=2026,
    )
    return profile, enrollment, grade


def target_level(framework, code):
    return PerformanceLevelDefinition.objects.get(framework=framework, code=code)


def create_payload(grade, *, target='ME1', term=3, year=2026, academic_grade=10):
    return {
        'continuity_code': grade.student_subject.continuity_code,
        'target_level_definition': target_level(grade.framework, target).id,
        'target_term': term,
        'target_year': year,
        'target_academic_grade': academic_grade,
        'action_plan': 'Practise twice each week and review teacher feedback.',
    }


@pytest.mark.django_db
def test_create_resolves_target_level_code_within_the_current_framework():
    """Catches requiring an internal definition ID that frontend clients cannot discover."""
    profile, _enrollment, grade = learner_with_evidence(level='ME2')
    client = APIClient()
    client.force_authenticate(profile.user)
    payload = create_payload(grade)
    payload.pop('target_level_definition')
    payload['target_level'] = 'ME1'

    response = client.post(GOALS_URL, payload, format='json')

    assert response.status_code == 201
    assert response.data['data']['target_level']['code'] == 'ME1'


def test_academic_goal_model_is_registered():
    """Catches removing the persistence boundary for academic improvement goals."""
    model_names = {model.__name__ for model in apps.get_app_config('students').get_models()}

    assert 'AcademicGoal' in model_names


def test_active_identity_constraint_is_unconditional_and_mysql_safe():
    """Catches replacing the nullable identity pattern with a partial unique constraint."""
    constraint = next(
        item
        for item in AcademicGoal._meta.constraints
        if item.name == 'students_active_goal_identity_uniq'
    )

    assert constraint.fields == ('learner', 'active_identity')
    assert constraint.condition is None
    assert AcademicGoal._meta.get_field('active_identity').null is True


@pytest.mark.django_db
def test_create_snapshots_latest_current_level_and_blocks_a_second_active_goal():
    """Catches spoofed current performance and duplicate active goals per continuity."""
    profile, enrollment, first = learner_with_evidence(level='AE1', term=1)
    latest = CBCGradeFactory(
        student_subject=enrollment,
        framework=first.framework,
        level='ME2',
        term=2,
        year=2026,
    )
    client = APIClient()
    client.force_authenticate(profile.user)

    created = client.post(GOALS_URL, create_payload(latest), format='json')
    duplicate = client.post(GOALS_URL, create_payload(latest), format='json')

    assert created.status_code == 201
    data = created.data['data']
    assert data['current_evidence'] == latest.id
    assert data['current_level'] == {
        'code': 'ME2',
        'rank': 5,
        'framework': {'code': latest.framework.code, 'version': latest.framework.version},
    }
    assert data['target_level']['code'] == 'ME1'
    assert data['status'] == 'active'
    assert data['ready_for_achievement'] is False
    assert duplicate.status_code == 400
    assert duplicate.data['error'] is True


@pytest.mark.django_db
def test_database_constraint_blocks_two_active_goals_but_allows_closed_history():
    """Catches application-only uniqueness that races under concurrent requests."""
    profile, _enrollment, grade = learner_with_evidence()
    current = target_level(grade.framework, grade.level)
    target = target_level(grade.framework, 'ME1')
    goal = AcademicGoalFactory(
        learner=profile,
        continuity_code='MAT',
        current_evidence=grade,
        current_level_definition=current,
        target_level_definition=target,
        created_by=profile.user,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AcademicGoalFactory(
                learner=profile,
                continuity_code='MAT',
                current_evidence=grade,
                current_level_definition=current,
                target_level_definition=target,
                created_by=profile.user,
            )

    goal.close(actor=profile.user)
    replacement = AcademicGoalFactory(
        learner=profile,
        continuity_code='MAT',
        current_evidence=grade,
        current_level_definition=current,
        target_level_definition=target,
        created_by=profile.user,
    )
    assert replacement.active_identity == 'MAT'


@pytest.mark.django_db
def test_create_rejects_lower_cross_framework_and_non_future_targets():
    """Catches regressions in same-framework, maintain-or-improve, and target ordering rules."""
    profile, _enrollment, grade = learner_with_evidence(level='ME2', term=2)
    client = APIClient()
    client.force_authenticate(profile.user)
    junior_framework = AssessmentFramework.objects.get(
        scope='junior_school',
        status=AssessmentFramework.STATUS_ACTIVE,
    )

    lower = client.post(GOALS_URL, create_payload(grade, target='AE1'), format='json')
    cross_framework_payload = create_payload(grade)
    cross_framework_payload['target_level_definition'] = target_level(
        junior_framework, 'ME1'
    ).id
    cross_framework = client.post(GOALS_URL, cross_framework_payload, format='json')
    same_period = client.post(
        GOALS_URL,
        create_payload(grade, target='ME1', term=2),
        format='json',
    )

    assert lower.status_code == 400
    assert 'lower' in str(lower.data['message']).casefold()
    assert cross_framework.status_code == 400
    assert 'framework' in str(cross_framework.data['message']).casefold()
    assert same_period.status_code == 400
    assert 'later' in str(same_period.data['message']).casefold()


@pytest.mark.django_db
def test_learner_crud_is_owned_and_delete_closes_without_erasing_history():
    """Catches cross-learner disclosure, mutable snapshots, or destructive deletion."""
    owner, _enrollment, grade = learner_with_evidence()
    other = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    owner_client = APIClient()
    owner_client.force_authenticate(owner.user)
    created = owner_client.post(GOALS_URL, create_payload(grade), format='json')
    goal_id = created.data['data']['id']

    updated = owner_client.patch(
        f'{GOALS_URL}{goal_id}/',
        {
            'action_plan': 'Attend weekly support and complete practice questions.',
            'status': 'achieved',
            'continuity_code': 'ENG',
        },
        format='json',
    )
    assert updated.status_code == 200
    assert updated.data['data']['action_plan'].startswith('Attend weekly')
    assert updated.data['data']['status'] == 'active'
    assert updated.data['data']['continuity_code'] == 'MAT'

    other_client = APIClient()
    other_client.force_authenticate(other.user)
    assert other_client.get(GOALS_URL).data['data'] == []
    assert other_client.get(f'{GOALS_URL}{goal_id}/').status_code == 404
    assert other_client.patch(
        f'{GOALS_URL}{goal_id}/', {'action_plan': 'Changed'}, format='json'
    ).status_code == 404

    closed = owner_client.delete(f'{GOALS_URL}{goal_id}/')
    assert closed.status_code == 200
    goal = AcademicGoal.objects.get(pk=goal_id)
    assert goal.status == AcademicGoal.STATUS_CLOSED
    assert goal.closed_at is not None
    assert goal.active_identity is None


@pytest.mark.django_db
def test_later_evidence_derives_readiness_but_achievement_requires_confirmation():
    """Catches automatic achievement or achievement without explicit learner confirmation."""
    profile, enrollment, grade = learner_with_evidence(level='ME2', term=1)
    client = APIClient()
    client.force_authenticate(profile.user)
    created = client.post(GOALS_URL, create_payload(grade), format='json')
    goal_id = created.data['data']['id']
    later = CBCGradeFactory(
        student_subject=enrollment,
        framework=grade.framework,
        level='ME1',
        term=2,
        year=2026,
    )

    ready = client.get(f'{GOALS_URL}{goal_id}/')
    goal = AcademicGoal.objects.get(pk=goal_id)
    assert ready.data['data']['ready_for_achievement'] is True
    assert ready.data['data']['readiness_evidence'] == later.id
    assert goal.status == AcademicGoal.STATUS_ACTIVE

    not_confirmed = client.post(
        f'{GOALS_URL}{goal_id}/confirm-achievement/',
        {'confirm': False},
        format='json',
    )
    confirmed = client.post(
        f'{GOALS_URL}{goal_id}/confirm-achievement/',
        {'confirm': True},
        format='json',
    )
    assert not_confirmed.status_code == 400
    assert confirmed.status_code == 200
    goal.refresh_from_db()
    assert goal.status == AcademicGoal.STATUS_ACHIEVED
    assert goal.achieved_at is not None
    assert goal.active_identity is None


@pytest.mark.django_db
def test_learner_cannot_confirm_achievement_before_target_is_ready():
    """Catches confirmation that ignores later evidence readiness."""
    profile, _enrollment, grade = learner_with_evidence(level='ME2')
    client = APIClient()
    client.force_authenticate(profile.user)
    goal_id = client.post(
        GOALS_URL, create_payload(grade), format='json'
    ).data['data']['id']

    response = client.post(
        f'{GOALS_URL}{goal_id}/confirm-achievement/',
        {'confirm': True},
        format='json',
    )

    assert response.status_code == 409
    assert AcademicGoal.objects.get(pk=goal_id).status == AcademicGoal.STATUS_ACTIVE


@pytest.mark.django_db
def test_assigned_counselor_has_read_only_access_to_selected_learner_goals():
    """Catches assignment bypasses or counselor mutations in the academic-goal domain."""
    profile, _enrollment, grade = learner_with_evidence()
    learner_client = APIClient()
    learner_client.force_authenticate(profile.user)
    goal_id = learner_client.post(
        GOALS_URL, create_payload(grade), format='json'
    ).data['data']['id']
    counselor = CounselorFactory()
    CounselorAssignmentFactory(counselor=counselor, student_profile=profile)
    counselor_client = APIClient()
    counselor_client.force_authenticate(counselor)

    listed = counselor_client.get(f'{GOALS_URL}?student_id={profile.user_id}')
    retrieved = counselor_client.get(f'{GOALS_URL}{goal_id}/')
    create_attempt = counselor_client.post(
        GOALS_URL, create_payload(grade), format='json'
    )
    update_attempt = counselor_client.patch(
        f'{GOALS_URL}{goal_id}/', {'action_plan': 'Counselor changed it.'}, format='json'
    )
    delete_attempt = counselor_client.delete(f'{GOALS_URL}{goal_id}/')

    assert listed.status_code == 200
    assert [item['id'] for item in listed.data['data']] == [goal_id]
    assert retrieved.status_code == 200
    assert create_attempt.status_code == 403
    assert update_attempt.status_code == 403
    assert delete_attempt.status_code == 403

    CounselorAssignment.objects.filter(counselor=counselor).update(is_active=False)
    assert counselor_client.get(
        f'{GOALS_URL}?student_id={profile.user_id}'
    ).status_code == 404
    assert counselor_client.get(f'{GOALS_URL}{goal_id}/').status_code == 404


@pytest.mark.django_db
def test_creation_snapshot_survives_permitted_evidence_edit_and_goal_close():
    """Catches goal history depending on a learner-editable CBCGrade row."""
    profile, enrollment, grade = learner_with_evidence(level='ME2', term=1)
    client = APIClient()
    client.force_authenticate(profile.user)
    created = client.post(GOALS_URL, create_payload(grade), format='json')
    goal_id = created.data['data']['id']

    snapshot = created.data['data']['creation_evidence_snapshot']
    assert snapshot == {
        'evidence_id': grade.id,
        'period': {'academic_grade': 10, 'year': 2026, 'term': 1},
        'level': {'code': 'ME2', 'rank': 5},
        'framework': {
            'id': grade.framework_id,
            'code': grade.framework.code,
            'version': grade.framework.version,
            'level_ranks': {
                'EE1': 8, 'EE2': 7, 'ME1': 6, 'ME2': 5,
                'AE1': 4, 'AE2': 3, 'BE1': 2, 'BE2': 1,
            },
        },
        'source': 'learner',
        'verification': {
            'confidence': 'learner_entered',
            'verified_by': None,
            'verified_school': None,
            'verified_at': None,
        },
        'recorded_at': grade.created_at.isoformat(),
    }

    edited = client.put(
        f'/api/v1/students/my-subjects/{enrollment.id}/grades/{grade.id}/',
        {'term': 1, 'year': 2026, 'level': 'AE1', 'raw_score': None},
        format='json',
    )
    updated = client.patch(
        f'{GOALS_URL}{goal_id}/',
        {'action_plan': 'Keep the historical baseline and adjust the weekly plan.'},
        format='json',
    )
    closed = client.delete(f'{GOALS_URL}{goal_id}/')

    assert edited.status_code == 200
    assert updated.status_code == 200
    assert updated.data['data']['creation_evidence_snapshot'] == snapshot
    assert closed.status_code == 200
    assert closed.data['data']['creation_evidence_snapshot'] == snapshot


@pytest.mark.django_db
def test_deleted_creation_evidence_does_not_break_readiness_or_confirmation():
    """Catches a goal revoking deletion or losing its baseline after SET_NULL."""
    profile, enrollment, grade = learner_with_evidence(level='ME2', term=1)
    client = APIClient()
    client.force_authenticate(profile.user)
    goal_id = client.post(
        GOALS_URL, create_payload(grade), format='json'
    ).data['data']['id']
    later = CBCGradeFactory(
        student_subject=enrollment,
        framework=grade.framework,
        level='ME1',
        term=2,
        year=2026,
    )

    deleted = client.delete(
        f'/api/v1/students/my-subjects/{enrollment.id}/grades/{grade.id}/'
    )
    ready = client.get(f'{GOALS_URL}{goal_id}/')
    confirmed = client.post(
        f'{GOALS_URL}{goal_id}/confirm-achievement/',
        {'confirm': True},
        format='json',
    )

    assert deleted.status_code == 200
    assert deleted.data == {'data': None, 'error': None, 'message': 'Grade deleted.'}
    assert ready.status_code == 200
    assert ready.data['data']['current_evidence'] is None
    assert ready.data['data']['ready_for_achievement'] is True
    assert ready.data['data']['readiness_evidence'] == later.id
    assert confirmed.status_code == 200
    achieved = confirmed.data['data']
    assert achieved['status'] == 'achieved'
    assert achieved['ready_for_achievement'] is True
    assert achieved['readiness_evidence'] == later.id
    assert achieved['achievement_evidence_snapshot']['evidence_id'] == later.id
    assert achieved['confirmed_by'] == profile.user_id


@pytest.mark.django_db
def test_model_and_database_reject_lifecycle_bypasses():
    """Catches direct state jumps and incoherent terminal timestamp identities."""
    goal = AcademicGoalFactory()

    goal.status = AcademicGoal.STATUS_ACHIEVED
    with pytest.raises(ValidationError, match='lifecycle transition'):
        goal.save()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AcademicGoal.objects.filter(pk=goal.pk).update(
                status=AcademicGoal.STATUS_ACHIEVED,
                active_identity=None,
                achieved_at=None,
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AcademicGoal.objects.filter(pk=goal.pk).update(
                status=AcademicGoal.STATUS_CLOSED,
                active_identity=None,
                achieved_at=goal.created_at,
                closed_at=goal.created_at,
            )


@pytest.mark.django_db
def test_new_goals_cannot_claim_the_legacy_migration_exemption():
    """Catches callers fabricating the migration-only lifecycle provenance flag."""
    with pytest.raises(ValidationError, match='legacy'):
        AcademicGoalFactory(
            status=AcademicGoal.STATUS_ACHIEVED,
            legacy_lifecycle_unverifiable=True,
        )

@pytest.mark.django_db
def test_domain_achievement_requires_owner_actor_and_ready_evidence():
    """Catches callers bypassing learner confirmation or readiness below the API."""
    profile, enrollment, grade = learner_with_evidence(level='ME2', term=1)
    goal = AcademicGoalFactory(
        current_evidence=grade,
        learner=profile,
        continuity_code=enrollment.continuity_code,
        created_by=profile.user,
    )

    with pytest.raises(ValidationError, match='not ready'):
        goal.mark_achieved(actor=profile.user)

    later = CBCGradeFactory(
        student_subject=enrollment,
        framework=grade.framework,
        level='ME1',
        term=2,
        year=2026,
    )
    outsider = VerifiedUserFactory(role='student')
    with pytest.raises(ValidationError, match='learner'):
        goal.mark_achieved(actor=outsider)

    goal.mark_achieved(actor=profile.user)
    goal.refresh_from_db()
    assert goal.confirmed_by_id == profile.user_id
    assert goal.achievement_evidence_snapshot['evidence_id'] == later.id

    goal.achievement_evidence_snapshot = {
        **goal.achievement_evidence_snapshot,
        'evidence_id': grade.id,
    }
    with pytest.raises(ValidationError, match='immutable'):
        goal.save(update_fields=['achievement_evidence_snapshot'])


@pytest.mark.django_db
def test_admin_is_view_only_for_academic_goals():
    """Catches Django admin paths that mutate learner-owned lifecycle state."""
    request = RequestFactory().get('/admin/students/academicgoal/')
    request.user = SystemAdminFactory()
    model_admin = AcademicGoalAdmin(AcademicGoal, admin.site)
    goal = AcademicGoalFactory()

    assert model_admin.has_view_permission(request, goal) is True
    assert model_admin.has_add_permission(request) is False
    assert model_admin.has_change_permission(request, goal) is False
    assert model_admin.has_delete_permission(request, goal) is False


@pytest.mark.django_db
def test_target_snapshot_and_readiness_do_not_drift_with_live_definition_edits():
    """Catches unrelated goal saves recopying mutable framework definitions."""
    profile, enrollment, grade = learner_with_evidence(level='ME2', term=1)
    client = APIClient()
    client.force_authenticate(profile.user)
    created = client.post(GOALS_URL, create_payload(grade), format='json')
    goal_id = created.data['data']['id']
    target = target_level(grade.framework, 'ME1')
    target.code = 'MEX'
    target.rank = 9
    target.save(update_fields=['code', 'rank'])
    later = CBCGradeFactory(
        student_subject=enrollment,
        framework=grade.framework,
        level='ME1',
        term=2,
        year=2026,
    )

    updated = client.patch(
        f'{GOALS_URL}{goal_id}/',
        {'action_plan': 'Only this plan text changes.'},
        format='json',
    )

    assert updated.status_code == 200
    assert updated.data['data']['target_level']['code'] == 'ME1'
    assert updated.data['data']['target_level']['rank'] == 6
    assert updated.data['data']['ready_for_achievement'] is True
    assert updated.data['data']['readiness_evidence'] == later.id


@pytest.mark.django_db
def test_explicit_target_change_refreshes_snapshot_and_revalidates():
    """Catches implicit or unvalidated target snapshot refreshes."""
    profile, _enrollment, grade = learner_with_evidence(level='AE1', term=1)
    client = APIClient()
    client.force_authenticate(profile.user)
    goal_id = client.post(
        GOALS_URL, create_payload(grade, target='ME2'), format='json'
    ).data['data']['id']

    changed = client.patch(
        f'{GOALS_URL}{goal_id}/', {'target_level': 'ME1'}, format='json'
    )
    invalid = client.patch(
        f'{GOALS_URL}{goal_id}/', {'target_level': 'BE1'}, format='json'
    )

    assert changed.status_code == 200
    assert changed.data['data']['target_level']['code'] == 'ME1'
    assert changed.data['data']['target_level']['rank'] == 6
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_stale_terminal_transition_cannot_overwrite_achievement():
    """Catches confirm-vs-close lost updates on databases with row locking."""
    profile, enrollment, grade = learner_with_evidence(level='ME2', term=1)
    goal = AcademicGoalFactory(
        current_evidence=grade,
        learner=profile,
        continuity_code=enrollment.continuity_code,
        created_by=profile.user,
    )
    stale = AcademicGoal.objects.get(pk=goal.pk)
    CBCGradeFactory(
        student_subject=enrollment,
        framework=grade.framework,
        level='ME1',
        term=2,
        year=2026,
    )
    goal.mark_achieved(actor=profile.user)

    with pytest.raises(ValidationError, match='active'):
        stale.close(actor=profile.user)

    stale.refresh_from_db()
    assert stale.status == AcademicGoal.STATUS_ACHIEVED
    assert stale.achieved_at is not None
    assert stale.closed_at is None


@pytest.mark.django_db
def test_academic_goal_factory_defaults_create_a_valid_goal():
    """Catches independently generated learner, continuity, and evidence defaults."""
    goal = AcademicGoalFactory()

    assert goal.learner_id == goal.current_evidence.student_subject.student_profile_id
    assert goal.continuity_code == goal.current_evidence.student_subject.continuity_code


@pytest.mark.django_db
def test_goal_list_readiness_queries_are_bounded(django_assert_num_queries):
    """Catches per-goal evidence and definition lookups during list serialization."""
    profile = StudentProfileFactory(user=VerifiedUserFactory(role='student'), grade=10)
    for index in range(5):
        continuity_code = f'GQ{index}'
        enrollment = StudentSubjectFactory(
            student_profile=profile,
            subject=SubjectFactory(
                code=f'{continuity_code}10',
                continuity_code=continuity_code,
                grade=10,
            ),
        )
        current = CBCGradeFactory(
            student_subject=enrollment, level='ME2', term=1, year=2026
        )
        AcademicGoalFactory(
            current_evidence=current,
            learner=profile,
            continuity_code=continuity_code,
            created_by=profile.user,
        )
        CBCGradeFactory(
            student_subject=enrollment,
            framework=current.framework,
            level='ME1',
            term=2,
            year=2026,
        )

    client = APIClient()
    client.force_authenticate(profile.user)
    with django_assert_num_queries(3):
        response = client.get(GOALS_URL)

    assert response.status_code == 200
    assert len(response.data['data']) == 5
    assert all(item['ready_for_achievement'] for item in response.data['data'])
