import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import VerifiedUserFactory, ParentFactory

pytestmark = pytest.mark.django_db


def _auth(client, user):
    token = str(RefreshToken.for_user(user).access_token)
    client.cookies['access_token'] = token


class TestParentChildrenView:
    def test_returns_empty_list(self, client):
        parent = ParentFactory()
        _auth(client, parent)
        r = client.get(reverse('parent-children'))
        assert r.status_code == 200
        assert r.json()['data'] == []

    def test_requires_auth(self, client):
        r = client.get(reverse('parent-children'))
        assert r.status_code == 401

    def test_student_cannot_access(self, client):
        student = VerifiedUserFactory(role='student')
        _auth(client, student)
        r = client.get(reverse('parent-children'))
        assert r.status_code == 403
