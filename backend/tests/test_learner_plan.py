import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from guidance.models import (
    FrameworkVersion,
    LearnerCombinationChoice,
    LearnerPlan,
    SubjectCombination,
)
from tests.factories import StudentProfileFactory, UserFactory, VerifiedUserFactory


pytestmark = pytest.mark.django_db

PLAN_URL = '/api/v1/students/plan/'
MILESTONES_URL = '/api/v1/students/plan/milestones/'


def client_for(profile):
    client = APIClient()
    client.force_authenticate(profile.user)
    return client


def provisional_choice(profile, index=0):
    combinations = SubjectCombination.objects.filter(
        framework_version=FrameworkVersion.objects.current(),
        is_active=True,
        track__is_active=True,
    ).order_by('pk')
    return LearnerCombinationChoice.objects.create(
        student_profile=profile,
        combination=combinations[index],
        status=LearnerCombinationChoice.STATUS_PROVISIONAL,
    )


class TestLearnerPlanPermissions:
    def test_unauthenticated_is_rejected(self):
        assert APIClient().get(PLAN_URL).status_code == 401

    def test_non_student_is_rejected(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='counselor'))
        assert client.get(PLAN_URL).status_code == 403

    def test_unverified_student_is_rejected(self):
        profile = StudentProfileFactory(
            user=UserFactory(role='student', is_email_verified=False)
        )
        assert client_for(profile).get(PLAN_URL).status_code == 403


class TestLearnerPlanFlow:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )
        self.client = client_for(self.profile)

    def test_get_returns_null_before_plan_creation(self):
        response = self.client.get(PLAN_URL)
        assert response.status_code == 200
        assert response.data['data'] is None

    def test_plan_requires_a_provisional_choice(self):
        response = self.client.put(
            PLAN_URL,
            {'learner_reason': 'This option fits my goals.'},
            format='json',
        )
        assert response.status_code == 400

    def test_create_plan_uses_current_provisional_choice(self):
        choice = provisional_choice(self.profile)
        response = self.client.put(
            PLAN_URL,
            {
                'learner_reason': 'I want to investigate these subjects.',
                'review_status': 'ready_for_review',
            },
            format='json',
        )

        assert response.status_code == 201
        assert response.data['data']['provisional_choice']['id'] == choice.pk
        assert response.data['data']['learner_reason'] == (
            'I want to investigate these subjects.'
        )
        assert response.data['data']['review_status'] == 'ready_for_review'
        assert response.data['data']['milestones'] == []

    def test_update_plan_and_reject_forged_reviewed_status(self):
        provisional_choice(self.profile)
        self.client.put(PLAN_URL, {'learner_reason': 'Initial reason'}, format='json')

        updated = self.client.put(
            PLAN_URL,
            {'learner_reason': 'Updated after comparison', 'review_status': 'draft'},
            format='json',
        )
        rejected = self.client.put(
            PLAN_URL,
            {'review_status': 'reviewed'},
            format='json',
        )

        assert updated.status_code == 200
        assert updated.data['data']['learner_reason'] == 'Updated after comparison'
        assert rejected.status_code == 400

    def test_editing_a_reviewed_plan_returns_it_to_draft(self):
        choice = provisional_choice(self.profile)
        plan = LearnerPlan.objects.create(
            student_profile=self.profile,
            provisional_choice=choice,
            learner_reason='Reviewed reason',
            review_status=LearnerPlan.STATUS_REVIEWED,
            reviewed_at=timezone.now(),
        )

        response = self.client.put(
            PLAN_URL,
            {'learner_reason': 'Changed after review'},
            format='json',
        )

        plan.refresh_from_db()
        assert response.status_code == 200
        assert plan.review_status == LearnerPlan.STATUS_DRAFT
        assert plan.reviewed_at is None

    def test_changing_provisional_choice_repoints_and_resets_plan(self):
        first = provisional_choice(self.profile, 0)
        self.client.put(
            PLAN_URL,
            {'review_status': 'ready_for_review'},
            format='json',
        )
        second_combination = SubjectCombination.objects.filter(
            framework_version=FrameworkVersion.objects.current()
        ).exclude(pk=first.combination_id).order_by('pk').first()
        second = LearnerCombinationChoice.objects.create(
            student_profile=self.profile,
            combination=second_combination,
        )

        response = self.client.put(
            f'/api/v1/students/combination-choices/{second.pk}/provisional/',
            {},
            format='json',
        )

        assert response.status_code == 200
        plan = LearnerPlan.objects.get(student_profile=self.profile)
        assert plan.provisional_choice == second
        assert plan.review_status == 'draft'

    def test_other_learner_cannot_access_plan_milestones(self):
        provisional_choice(self.profile)
        plan_response = self.client.put(PLAN_URL, {}, format='json')
        milestone = self.client.post(
            MILESTONES_URL,
            {'title': 'Review school offerings'},
            format='json',
        ).data['data']
        other = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )

        response = client_for(other).put(
            f'{MILESTONES_URL}{milestone["id"]}/',
            {'is_complete': True},
            format='json',
        )

        assert plan_response.status_code == 201
        assert response.status_code == 404


class TestPlanMilestones:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )
        self.client = client_for(self.profile)

    def create_plan(self):
        provisional_choice(self.profile)
        return self.client.put(PLAN_URL, {}, format='json')

    def test_milestone_requires_an_existing_plan(self):
        response = self.client.post(
            MILESTONES_URL,
            {'title': 'Discuss with counsellor'},
            format='json',
        )
        assert response.status_code == 404

    def test_create_complete_reopen_and_delete_milestone(self):
        self.create_plan()
        created = self.client.post(
            MILESTONES_URL,
            {
                'title': 'Compare pilot school offerings',
                'due_date': '2026-09-15',
                'position': 1,
            },
            format='json',
        )
        milestone_id = created.data['data']['id']
        completed = self.client.put(
            f'{MILESTONES_URL}{milestone_id}/',
            {'is_complete': True},
            format='json',
        )
        reopened = self.client.put(
            f'{MILESTONES_URL}{milestone_id}/',
            {'is_complete': False},
            format='json',
        )
        deleted = self.client.delete(f'{MILESTONES_URL}{milestone_id}/')

        assert created.status_code == 201
        assert completed.data['data']['completed_at'] is not None
        assert reopened.data['data']['completed_at'] is None
        assert deleted.status_code == 204

    def test_title_and_position_are_validated(self):
        self.create_plan()
        response = self.client.post(
            MILESTONES_URL,
            {'title': '', 'position': -1},
            format='json',
        )
        assert response.status_code == 400

    def test_complete_milestone_created_with_server_timestamp(self):
        self.create_plan()
        response = self.client.post(
            MILESTONES_URL,
            {'title': 'Confirm final selection', 'is_complete': True},
            format='json',
        )

        assert response.status_code == 201
        assert response.data['data']['completed_at'] is not None
