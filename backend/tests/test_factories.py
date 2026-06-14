import pytest
from django.contrib.auth import get_user_model
from accounts.models import School, StudentProfile

User = get_user_model()


@pytest.mark.django_db
class TestUserFactory:
    def test_creates_student(self):
        from tests.factories import UserFactory
        user = UserFactory(role='student')
        assert user.pk is not None
        assert user.role == 'student'
        assert user.email.endswith('@example.com')
        assert user.is_email_verified is False

    def test_creates_verified_student(self):
        from tests.factories import VerifiedUserFactory
        user = VerifiedUserFactory(role='student')
        assert user.is_email_verified is True

    def test_creates_counselor(self):
        from tests.factories import UserFactory
        user = UserFactory(role='counselor')
        assert user.role == 'counselor'
        assert user.county == 'kiambu'

    def test_emails_are_unique(self):
        from tests.factories import UserFactory
        u1 = UserFactory(role='student')
        u2 = UserFactory(role='student')
        assert u1.email != u2.email

    def test_creates_system_admin(self):
        from tests.factories import UserFactory
        user = UserFactory(role='system_admin')
        assert user.county is None


@pytest.mark.django_db
class TestSchoolFactory:
    def test_creates_school(self):
        from tests.factories import SchoolFactory
        school = SchoolFactory()
        assert school.pk is not None
        assert school.county in ('kiambu', 'muranga', 'nyeri', 'kirinyaga', 'nyandarua')

    def test_school_codes_are_unique(self):
        from tests.factories import SchoolFactory
        s1 = SchoolFactory()
        s2 = SchoolFactory()
        assert s1.school_code != s2.school_code


@pytest.mark.django_db
class TestStudentProfileFactory:
    def test_creates_self_guided_profile(self):
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory(mode='self_guided')
        assert profile.mode == 'self_guided'
        assert profile.school is None
        assert profile.grade in (9, 10)

    def test_creates_school_linked_profile(self):
        from tests.factories import StudentProfileFactory, SchoolFactory
        school = SchoolFactory()
        profile = StudentProfileFactory(mode='school_linked', school=school)
        assert profile.mode == 'school_linked'
        assert profile.school == school
