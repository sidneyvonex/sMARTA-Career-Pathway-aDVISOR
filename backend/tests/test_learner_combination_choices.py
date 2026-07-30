import pytest
from rest_framework.test import APIClient

from guidance.models import FrameworkVersion, LearnerCombinationChoice, SubjectCombination
from tests.factories import StudentProfileFactory, UserFactory, VerifiedUserFactory


pytestmark = pytest.mark.django_db

CHOICES_URL = '/api/v1/students/combination-choices/'


def client_for(profile):
    client = APIClient()
    client.force_authenticate(profile.user)
    return client


def current_combinations():
    framework = FrameworkVersion.objects.current()
    return list(
        SubjectCombination.objects.filter(
            framework_version=framework,
            is_active=True,
            track__is_active=True,
        ).order_by('pk')
    )


class TestLearnerCombinationChoicePermissions:
    def test_unauthenticated_is_rejected(self):
        assert APIClient().get(CHOICES_URL).status_code == 401

    def test_non_student_is_rejected(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='counselor'))
        assert client.get(CHOICES_URL).status_code == 403

    def test_unverified_student_is_rejected(self):
        profile = StudentProfileFactory(
            user=UserFactory(role='student', is_email_verified=False)
        )
        assert client_for(profile).get(CHOICES_URL).status_code == 403


class TestLearnerCombinationChoiceFlow:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )
        self.client = client_for(self.profile)

    def save(self, combination, reason=''):
        return self.client.post(
            CHOICES_URL,
            {'combination_id': combination.pk, 'learner_reason': reason},
            format='json',
        )

    def test_list_starts_empty(self):
        response = self.client.get(CHOICES_URL)
        assert response.status_code == 200
        assert response.data['data'] == []

    def test_create_defaults_to_saved_and_returns_combination(self):
        combination = current_combinations()[0]
        response = self.save(combination, 'It matches the subjects I enjoy.')

        assert response.status_code == 201
        assert response.data['data']['status'] == 'saved'
        assert response.data['data']['combination']['id'] == combination.pk
        assert response.data['data']['learner_reason'] == (
            'It matches the subjects I enjoy.'
        )

    def test_duplicate_combination_is_rejected(self):
        combination = current_combinations()[0]
        assert self.save(combination).status_code == 201
        assert self.save(combination).status_code == 400

    def test_maximum_three_choices(self):
        combinations = current_combinations()[:4]
        assert [self.save(item).status_code for item in combinations[:3]] == [
            201,
            201,
            201,
        ]
        response = self.save(combinations[3])
        assert response.status_code == 400
        assert 'maximum of three' in str(response.data['message']).lower()

    def test_inactive_combination_is_rejected(self):
        combination = current_combinations()[0]
        combination.is_active = False
        combination.save(update_fields=['is_active'])
        assert self.save(combination).status_code == 404

    def test_setting_provisional_demotes_the_previous_choice(self):
        first, second = current_combinations()[:2]
        first_choice = self.save(first).data['data']
        second_choice = self.save(second).data['data']

        first_response = self.client.put(
            f'{CHOICES_URL}{first_choice["id"]}/provisional/',
            {},
            format='json',
        )
        second_response = self.client.put(
            f'{CHOICES_URL}{second_choice["id"]}/provisional/',
            {},
            format='json',
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert LearnerCombinationChoice.objects.get(
            pk=first_choice['id']
        ).status == 'saved'
        assert LearnerCombinationChoice.objects.get(
            pk=second_choice['id']
        ).status == 'provisional'

    def test_saved_choice_can_be_removed(self):
        choice = self.save(current_combinations()[0]).data['data']
        response = self.client.delete(f'{CHOICES_URL}{choice["id"]}/')
        assert response.status_code == 204
        assert not LearnerCombinationChoice.objects.filter(pk=choice['id']).exists()

    def test_provisional_choice_must_be_changed_before_removal(self):
        choice = self.save(current_combinations()[0]).data['data']
        self.client.put(
            f'{CHOICES_URL}{choice["id"]}/provisional/',
            {},
            format='json',
        )
        response = self.client.delete(f'{CHOICES_URL}{choice["id"]}/')
        assert response.status_code == 400

    def test_cannot_change_or_remove_another_learners_choice(self):
        other = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            grade=9,
        )
        choice = LearnerCombinationChoice.objects.create(
            student_profile=other,
            combination=current_combinations()[0],
        )
        assert self.client.put(
            f'{CHOICES_URL}{choice.pk}/provisional/',
            {},
            format='json',
        ).status_code == 404
        assert self.client.delete(f'{CHOICES_URL}{choice.pk}/').status_code == 404
