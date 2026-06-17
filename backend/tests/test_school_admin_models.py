import pytest
from accounts.models import School

pytestmark = pytest.mark.django_db


class TestSchoolModelFields:
    def test_school_has_logo_url(self):
        school = School.objects.create(
            name='Test School', county='kiambu', school_code='TST0001',
        )
        assert school.logo_url is None
        school.logo_url = 'https://example.com/logo.png'
        school.save()
        school.refresh_from_db()
        assert school.logo_url == 'https://example.com/logo.png'

    def test_school_has_phone(self):
        school = School.objects.create(
            name='Test School', county='kiambu', school_code='TST0002',
        )
        assert school.phone == ''
        school.phone = '+254712345678'
        school.save()
        school.refresh_from_db()
        assert school.phone == '+254712345678'

    def test_school_has_email(self):
        school = School.objects.create(
            name='Test School', county='kiambu', school_code='TST0003',
        )
        assert school.email == ''
        school.email = 'info@testschool.ac.ke'
        school.save()
        school.refresh_from_db()
        assert school.email == 'info@testschool.ac.ke'
