import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from tests.factories import SchoolAdminFactory, SchoolFactory, StudentProfileFactory, CounselorFactory

pytestmark = pytest.mark.django_db


class TestSchoolProfileView:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Starehe Boys', county='nairobi', school_code='NAI001')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_get_school_profile(self):
        response = self.client.get('/api/v1/school-admin/school/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['name'] == 'Starehe Boys'
        assert data['county'] == 'nairobi'
        assert data['school_code'] == 'NAI001'
        assert data['logo_url'] is None
        assert data['student_count'] == 0
        assert data['counselor_count'] == 0

    def test_get_school_profile_with_counts(self):
        CounselorFactory(school=self.school)
        CounselorFactory(school=self.school)
        StudentProfileFactory(school=self.school, mode='school_linked')
        response = self.client.get('/api/v1/school-admin/school/')
        data = response.data['data']
        assert data['student_count'] == 1
        assert data['counselor_count'] == 2

    def test_patch_school_profile(self):
        response = self.client.patch('/api/v1/school-admin/school/', {
            'name': 'Starehe Boys Centre',
            'phone': '+254712345678',
            'email': 'info@starehe.ac.ke',
        })
        assert response.status_code == 200
        data = response.data['data']
        assert data['name'] == 'Starehe Boys Centre'
        assert data['phone'] == '+254712345678'
        assert data['email'] == 'info@starehe.ac.ke'

    def test_patch_rejects_school_code_change(self):
        response = self.client.patch('/api/v1/school-admin/school/', {
            'school_code': 'HACK001',
        })
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.school_code == 'NAI001'

    def test_patch_rejects_county_change(self):
        response = self.client.patch('/api/v1/school-admin/school/', {
            'county': 'mombasa',
        })
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.county == 'nairobi'

    def test_requires_school_admin_role(self):
        student_client = APIClient()
        student = CounselorFactory(school=self.school)
        student_client.force_authenticate(student)
        response = student_client.get('/api/v1/school-admin/school/')
        assert response.status_code == 403

    def test_admin_without_school_gets_404(self):
        orphan = SchoolAdminFactory(school=None)
        self.client.force_authenticate(orphan)
        response = self.client.get('/api/v1/school-admin/school/')
        assert response.status_code == 404
