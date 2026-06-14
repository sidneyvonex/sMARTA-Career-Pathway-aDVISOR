import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='TestPass123!',
            first_name='Jane',
            last_name='Doe',
            role='student',
            county='kiambu',
        )
        assert user.email == 'student@example.com'
        assert user.check_password('TestPass123!')
        assert user.role == 'student'
        assert user.county == 'kiambu'
        assert user.is_email_verified is False
        assert user.username is None

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == 'email'

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match='Email is required'):
            User.objects.create_user(email='', password='TestPass123!', role='student')

    def test_email_normalized_on_create(self):
        user = User.objects.create_user(
            email='Test@EXAMPLE.COM',
            password='TestPass123!',
            role='student',
            county='nyeri',
        )
        assert user.email == 'test@example.com'

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@cbcguidance.co.ke',
            password='AdminPass123!',
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == 'system_admin'

    def test_str_returns_email(self):
        user = User.objects.create_user(
            email='counselor@school.co.ke',
            password='TestPass123!',
            role='counselor',
            county='muranga',
        )
        assert str(user) == 'counselor@school.co.ke'

    def test_system_admin_county_nullable(self):
        admin = User.objects.create_user(
            email='sysadmin@cbcguidance.co.ke',
            password='TestPass123!',
            role='system_admin',
            county=None,
        )
        assert admin.county is None
