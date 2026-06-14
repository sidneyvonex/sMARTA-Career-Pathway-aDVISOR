import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import School, StudentProfile

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def school(db):
    return School.objects.create(name='Kiambu High', county='kiambu', school_code='KIA-001')


@pytest.mark.django_db
class TestStudentRegistration:
    def test_self_guided_registration_returns_201(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'student@test.com',
            'password': 'TestPass123!',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
        }, format='json')
        assert response.status_code == 201

    def test_self_guided_creates_user_and_profile(self, client):
        client.post('/api/v1/auth/register/', {
            'email': 'jane@test.com',
            'password': 'TestPass123!',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
        }, format='json')
        user = User.objects.get(email='jane@test.com')
        assert user.is_email_verified is False
        assert user.student_profile.mode == 'self_guided'
        assert user.student_profile.school is None

    def test_sends_verification_email(self, client, mailoutbox):
        client.post('/api/v1/auth/register/', {
            'email': 'verify@test.com',
            'password': 'TestPass123!',
            'first_name': 'A',
            'last_name': 'B',
            'role': 'student',
            'county': 'nyeri',
            'grade': 10,
        }, format='json')
        assert len(mailoutbox) == 1
        assert 'verify@test.com' in mailoutbox[0].to

    def test_school_linked_registration(self, client, school):
        response = client.post('/api/v1/auth/register/', {
            'email': 'linked@test.com',
            'password': 'TestPass123!',
            'first_name': 'John',
            'last_name': 'K',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
            'school_code': 'KIA-001',
        }, format='json')
        assert response.status_code == 201
        user = User.objects.get(email='linked@test.com')
        assert user.student_profile.mode == 'school_linked'
        assert user.student_profile.school == school

    def test_invalid_county_returns_400(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'bad@test.com',
            'password': 'TestPass123!',
            'first_name': 'X',
            'last_name': 'Y',
            'role': 'student',
            'county': 'mombasa',
            'grade': 9,
        }, format='json')
        assert response.status_code == 400

    def test_duplicate_email_returns_400(self, client):
        data = {
            'email': 'dup@test.com',
            'password': 'TestPass123!',
            'first_name': 'A',
            'last_name': 'B',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
        }
        client.post('/api/v1/auth/register/', data, format='json')
        response = client.post('/api/v1/auth/register/', data, format='json')
        assert response.status_code == 400

    def test_invalid_school_code_returns_400(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'x@test.com',
            'password': 'TestPass123!',
            'first_name': 'A',
            'last_name': 'B',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
            'school_code': 'INVALID-999',
        }, format='json')
        assert response.status_code == 400

    def test_non_student_role_rejected_from_register(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'c@test.com',
            'password': 'TestPass123!',
            'first_name': 'A',
            'last_name': 'B',
            'role': 'counselor',
            'county': 'kiambu',
            'grade': 9,
        }, format='json')
        assert response.status_code == 400

    def test_school_county_mismatch_returns_400(self, client):
        School.objects.create(name='Nyeri High', county='nyeri', school_code='NYE-001')
        response = client.post('/api/v1/auth/register/', {
            'email': 'mismatch@test.com',
            'password': 'TestPass123!',
            'first_name': 'A',
            'last_name': 'B',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
            'school_code': 'NYE-001',
        }, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_returns_200_and_sets_cookies(self, client):
        from tests.factories import UserFactory
        user = UserFactory(email='login@test.com', is_email_verified=True)
        response = client.post('/api/v1/auth/login/', {
            'email': 'login@test.com',
            'password': 'TestPass123!',
        }, format='json')
        assert response.status_code == 200
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies
        assert response.cookies['access_token']['httponly'] is True

    def test_login_returns_user_data(self, client):
        from tests.factories import UserFactory
        UserFactory(email='me@test.com', role='student', is_email_verified=True)
        response = client.post('/api/v1/auth/login/', {
            'email': 'me@test.com', 'password': 'TestPass123!',
        }, format='json')
        assert response.data['data']['user']['role'] == 'student'

    def test_login_wrong_password_returns_401(self, client):
        from tests.factories import UserFactory
        UserFactory(email='wrong@test.com')
        response = client.post('/api/v1/auth/login/', {
            'email': 'wrong@test.com', 'password': 'WrongPass!',
        }, format='json')
        assert response.status_code == 401

    def test_login_nonexistent_email_returns_401(self, client):
        response = client.post('/api/v1/auth/login/', {
            'email': 'nobody@test.com', 'password': 'TestPass123!',
        }, format='json')
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_clears_cookies(self, client):
        from tests.factories import UserFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        user = UserFactory(email='logout@test.com')
        refresh = RefreshToken.for_user(user)
        client.cookies['access_token'] = str(refresh.access_token)
        client.cookies['refresh_token'] = str(refresh)
        response = client.post('/api/v1/auth/logout/')
        assert response.status_code == 200
        assert response.cookies['access_token'].value == ''
        assert response.cookies['refresh_token'].value == ''


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_sets_new_access_cookie(self, client):
        from tests.factories import UserFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        user = UserFactory(email='refresh@test.com')
        refresh = RefreshToken.for_user(user)
        client.cookies['refresh_token'] = str(refresh)
        response = client.post('/api/v1/auth/token/refresh/')
        assert response.status_code == 200
        assert 'access_token' in response.cookies

    def test_refresh_without_cookie_returns_401(self, client):
        response = client.post('/api/v1/auth/token/refresh/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestMeView:
    def test_me_returns_user_data(self, client):
        from tests.factories import UserFactory
        from rest_framework_simplejwt.tokens import RefreshToken
        user = UserFactory(email='me2@test.com', role='counselor', is_email_verified=True)
        refresh = RefreshToken.for_user(user)
        client.cookies['access_token'] = str(refresh.access_token)
        response = client.get('/api/v1/auth/me/')
        assert response.status_code == 200
        assert response.data['data']['user']['email'] == 'me2@test.com'
        assert response.data['data']['user']['role'] == 'counselor'

    def test_me_unauthenticated_returns_401(self, client):
        response = client.get('/api/v1/auth/me/')
        assert response.status_code == 401
