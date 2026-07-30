from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from counselors.models import CounselorIntervention, CounselorNote
from tests.factories import (
    CounselorAssignmentFactory,
    CounselorFactory,
    CounselorNoteFactory,
    SchoolFactory,
    StudentProfileFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db


def _auth(client, user):
    token = str(RefreshToken.for_user(user).access_token)
    client.cookies['access_token'] = token


@pytest.fixture
def intervention_context():
    school = SchoolFactory()
    counselor = CounselorFactory(school=school)
    profile = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        school=school,
        mode='school_linked',
    )
    CounselorAssignmentFactory(
        counselor=counselor,
        student_profile=profile,
        school=school,
    )
    return counselor, profile


def test_intervention_is_separate_from_private_counselor_note(
    intervention_context,
):
    counselor, profile = intervention_context
    private_note = CounselorNoteFactory(
        counselor=counselor,
        student=profile.user,
        visible_to_parent=False,
    )
    intervention = CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_PLAN,
        action_agreed='Compare the two shortlisted combinations.',
        learner_visible=True,
        parent_visible=False,
    )

    assert CounselorNote.objects.filter(pk=private_note.pk).exists()
    assert intervention.learner_visible is True
    assert intervention.parent_visible is False


def test_completing_intervention_sets_completion_timestamp(
    intervention_context,
):
    counselor, profile = intervention_context
    intervention = CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_FOLLOW_UP,
        action_agreed='Confirm the school offering.',
    )

    intervention.status = CounselorIntervention.STATUS_COMPLETED
    intervention.save()

    assert intervention.completed_at is not None

    intervention.status = CounselorIntervention.STATUS_OPEN
    intervention.save()
    assert intervention.completed_at is None


def test_counselor_can_create_and_list_assigned_learner_intervention(
    client,
    intervention_context,
):
    counselor, profile = intervention_context
    _auth(client, counselor)
    follow_up_date = timezone.localdate() + timedelta(days=7)

    response = client.post(
        reverse('counselor-interventions'),
        {
            'student_id': profile.user_id,
            'category': 'academic_evidence',
            'action_agreed': 'Bring the latest mathematics evidence.',
            'follow_up_date': follow_up_date.isoformat(),
            'learner_visible': True,
            'parent_visible': True,
        },
        content_type='application/json',
    )

    assert response.status_code == 201
    assert response.json()['data']['status'] == 'open'
    assert response.json()['data']['follow_up_date'] == follow_up_date.isoformat()
    assert response.json()['data']['learner_visible'] is True
    assert response.json()['data']['parent_visible'] is True

    listed = client.get(reverse('counselor-interventions'))
    assert listed.status_code == 200
    assert [item['id'] for item in listed.json()['data']] == [
        response.json()['data']['id'],
    ]


def test_counselor_cannot_create_intervention_for_unassigned_learner(
    client,
    intervention_context,
):
    counselor, _ = intervention_context
    other_profile = StudentProfileFactory(
        user=VerifiedUserFactory(role='student')
    )
    _auth(client, counselor)

    response = client.post(
        reverse('counselor-interventions'),
        {
            'student_id': other_profile.user_id,
            'category': 'plan',
            'action_agreed': 'Create a learner plan.',
        },
        content_type='application/json',
    )

    assert response.status_code == 400
    assert CounselorIntervention.objects.count() == 0


def test_counselor_can_complete_own_intervention(
    client,
    intervention_context,
):
    counselor, profile = intervention_context
    intervention = CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_PLAN,
        action_agreed='Review the learner plan.',
    )
    _auth(client, counselor)

    response = client.patch(
        reverse('counselor-intervention-detail', args=[intervention.pk]),
        {'status': 'completed'},
        content_type='application/json',
    )

    assert response.status_code == 200
    assert response.json()['data']['status'] == 'completed'
    assert response.json()['data']['completed_at'] is not None


def test_counselor_cannot_update_another_counselors_intervention(
    client,
    intervention_context,
):
    counselor, profile = intervention_context
    other_counselor = CounselorFactory(school=profile.school)
    intervention = CounselorIntervention.objects.create(
        counselor=other_counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_PLAN,
        action_agreed='Private caseload action.',
    )
    _auth(client, counselor)

    response = client.patch(
        reverse('counselor-intervention-detail', args=[intervention.pk]),
        {'status': 'completed'},
        content_type='application/json',
    )

    assert response.status_code == 404


def test_learner_sees_only_learner_visible_interventions(
    client,
    intervention_context,
):
    counselor, profile = intervention_context
    visible = CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_PLAN,
        action_agreed='Review your milestone dates.',
        learner_visible=True,
    )
    CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_OTHER,
        action_agreed='Internal staff action.',
        learner_visible=False,
    )
    _auth(client, profile.user)

    response = client.get(reverse('student-interventions'))

    assert response.status_code == 200
    assert [item['id'] for item in response.json()['data']] == [visible.id]


def test_approved_parent_sees_only_parent_visible_interventions(
    client,
    intervention_context,
):
    from tests.factories import ParentFactory, ParentStudentLinkFactory

    counselor, profile = intervention_context
    parent = ParentFactory()
    ParentStudentLinkFactory(parent=parent, student=profile.user)
    visible = CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_PLAN,
        action_agreed='Discuss the reviewed learner plan.',
        parent_visible=True,
    )
    CounselorIntervention.objects.create(
        counselor=counselor,
        student=profile.user,
        category=CounselorIntervention.CATEGORY_OTHER,
        action_agreed='Counsellor-only action.',
        parent_visible=False,
    )
    _auth(client, parent)

    response = client.get(
        f'/api/v1/parents/children/{profile.user_id}/'
    )

    assert response.status_code == 200
    assert [item['id'] for item in response.json()['data']['interventions']] == [
        visible.id,
    ]
