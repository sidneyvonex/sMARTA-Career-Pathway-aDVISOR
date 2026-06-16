import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import VerifiedUserFactory

pytestmark = pytest.mark.django_db


def _auth(client, user):
    token = str(RefreshToken.for_user(user).access_token)
    client.cookies['access_token'] = token


class TestCounselorStudentsView:
    def test_returns_empty_list(self, client):
        counselor = VerifiedUserFactory(role='counselor')
        _auth(client, counselor)
        r = client.get(reverse('counselor-students'))
        assert r.status_code == 200
        assert r.json()['data'] == []

    def test_requires_auth(self, client):
        r = client.get(reverse('counselor-students'))
        assert r.status_code == 401

    def test_student_cannot_access(self, client):
        student = VerifiedUserFactory(role='student')
        _auth(client, student)
        r = client.get(reverse('counselor-students'))
        assert r.status_code == 403


class TestCounselorStatsView:
    def test_returns_zeroed_stats(self, client):
        counselor = VerifiedUserFactory(role='counselor')
        _auth(client, counselor)
        r = client.get(reverse('counselor-stats'))
        assert r.status_code == 200
        data = r.json()['data']
        assert data['total_students'] == 0
        assert data['assessments_done'] == 0
        assert data['students_needing_attention'] == 0
        assert data['notes_written'] == 0

    def test_requires_auth(self, client):
        r = client.get(reverse('counselor-stats'))
        assert r.status_code == 401

    def test_student_cannot_access_stats(self, client):
        student = VerifiedUserFactory(role='student')
        _auth(client, student)
        r = client.get(reverse('counselor-stats'))
        assert r.status_code == 403
