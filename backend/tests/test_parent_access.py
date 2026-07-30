import pytest
from rest_framework.test import APIClient

from parents.models import ParentStudentLink
from tests.factories import (
    ParentFactory,
    ParentStudentLinkFactory,
    StudentProfileFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db

ACCESS_URL = '/api/v1/students/parent-access/'


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class TestStudentParentAccessPermissions:
    def test_unauthenticated_is_rejected(self):
        assert APIClient().get(ACCESS_URL).status_code == 401

    def test_parent_is_rejected(self):
        assert client_for(ParentFactory()).get(ACCESS_URL).status_code == 403


class TestStudentParentAccessFlow:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
        )
        self.client = client_for(self.profile.user)
        self.link = ParentStudentLinkFactory(
            student=self.profile.user,
            status=ParentStudentLink.STATUS_PENDING,
            claimed_relationship=ParentStudentLink.RELATIONSHIP_GUARDIAN,
        )

    def test_list_exposes_claim_without_granting_access(self):
        response = self.client.get(ACCESS_URL)

        assert response.status_code == 200
        item = response.data['data'][0]
        assert item['parent_email'] == self.link.parent.email
        assert item['relationship_label'] == 'Guardian'
        assert item['status'] == 'pending_learner'
        assert item['learner_approved_at'] is None

    def test_learner_can_approve_pending_access(self):
        response = self.client.put(
            f'{ACCESS_URL}{self.link.pk}/approve/',
            {},
            format='json',
        )

        self.link.refresh_from_db()
        assert response.status_code == 200
        assert self.link.status == ParentStudentLink.STATUS_ACTIVE
        assert self.link.learner_approved_at is not None
        assert self.link.revoked_at is None

    def test_learner_can_revoke_access(self):
        self.link.status = ParentStudentLink.STATUS_ACTIVE
        self.link.save(update_fields=['status'])

        response = self.client.put(
            f'{ACCESS_URL}{self.link.pk}/revoke/',
            {},
            format='json',
        )

        self.link.refresh_from_db()
        assert response.status_code == 200
        assert self.link.status == ParentStudentLink.STATUS_REVOKED
        assert self.link.revoked_at is not None

    def test_other_learner_cannot_change_access(self):
        other = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
        )

        response = client_for(other.user).put(
            f'{ACCESS_URL}{self.link.pk}/approve/',
            {},
            format='json',
        )

        assert response.status_code == 404

    def test_revoked_access_cannot_be_reapproved(self):
        self.link.status = ParentStudentLink.STATUS_REVOKED
        self.link.save(update_fields=['status'])

        response = self.client.put(
            f'{ACCESS_URL}{self.link.pk}/approve/',
            {},
            format='json',
        )

        assert response.status_code == 400
