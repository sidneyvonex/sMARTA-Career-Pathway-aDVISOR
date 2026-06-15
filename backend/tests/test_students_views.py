import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import VerifiedUserFactory, UserFactory, StudentProfileFactory


@pytest.fixture
def client():
    return APIClient()


def make_auth_client(user):
    c = APIClient()
    refresh = RefreshToken.for_user(user)
    c.cookies['access_token'] = str(refresh.access_token)
    return c


@pytest.fixture
def verified_profile(db):
    user = VerifiedUserFactory(role='student')
    return StudentProfileFactory(user=user, grade=9)


@pytest.mark.django_db
class TestStudentProfileView:
    def test_get_profile_returns_200(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.get('/api/v1/students/profile/')
        assert response.status_code == 200
        assert response.data['data']['email'] == verified_profile.user.email
        assert response.data['data']['grade'] == 9

    def test_patch_updates_bio(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.patch('/api/v1/students/profile/', {'bio': 'I love science.'}, format='json')
        assert response.status_code == 200
        assert response.data['data']['bio'] == 'I love science.'

    def test_patch_bio_over_500_chars_rejected(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        response = c.patch('/api/v1/students/profile/', {'bio': 'x' * 501}, format='json')
        assert response.status_code == 400

    def test_patch_cannot_change_grade(self, verified_profile):
        c = make_auth_client(verified_profile.user)
        c.patch('/api/v1/students/profile/', {'grade': 10}, format='json')
        verified_profile.refresh_from_db()
        assert verified_profile.grade == 9

    def test_unverified_student_patch_returns_403(self, db):
        user = UserFactory(role='student', is_email_verified=False)
        StudentProfileFactory(user=user, grade=9)
        c = make_auth_client(user)
        response = c.patch('/api/v1/students/profile/', {'bio': 'hi'}, format='json')
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        response = client.get('/api/v1/students/profile/')
        assert response.status_code == 401

    def test_counselor_role_returns_403(self, db):
        user = VerifiedUserFactory(role='counselor')
        c = make_auth_client(user)
        response = c.get('/api/v1/students/profile/')
        assert response.status_code == 403
