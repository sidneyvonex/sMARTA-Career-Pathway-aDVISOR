import pytest
from rest_framework.test import APIClient
from tests.factories import (
    SystemAdminFactory, SchoolFactory, CounselorFactory,
    StudentProfileFactory, AuditLogFactory, VerifiedUserFactory,
    SchoolAdminFactory,
)
from system_admin.models import AuditLog
from accounts.models import School

pytestmark = pytest.mark.django_db


class TestDashboardView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_dashboard_returns_stats(self):
        SchoolFactory()
        SchoolFactory()
        VerifiedUserFactory(role='student')
        response = self.client.get('/api/v1/system-admin/dashboard/')
        assert response.status_code == 200
        data = response.data['data']
        assert 'users_by_role' in data
        assert 'schools_by_county' in data
        assert 'total_schools' in data
        assert data['total_schools'] == 2
        assert 'recent_signups' in data
        assert 'recent_audit' in data

    def test_dashboard_recent_audit_limited_to_10(self):
        for i in range(15):
            AuditLogFactory(actor=self.admin, target_id=i)
        response = self.client.get('/api/v1/system-admin/dashboard/')
        assert len(response.data['data']['recent_audit']) == 10

    def test_dashboard_requires_system_admin(self):
        client = APIClient()
        student = VerifiedUserFactory(role='student')
        client.force_authenticate(student)
        response = client.get('/api/v1/system-admin/dashboard/')
        assert response.status_code == 403

    def test_dashboard_excludes_inactive_schools_from_count(self):
        SchoolFactory(is_active=True)
        SchoolFactory(is_active=False)
        response = self.client.get('/api/v1/system-admin/dashboard/')
        assert response.data['data']['total_schools'] == 1


class TestSchoolListView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_list_all_schools(self):
        SchoolFactory(name='Alpha School')
        SchoolFactory(name='Beta School')
        response = self.client.get('/api/v1/system-admin/schools/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['total'] == 2
        assert len(data['results']) == 2

    def test_filter_by_county(self):
        SchoolFactory(county='kiambu')
        SchoolFactory(county='nyeri')
        response = self.client.get('/api/v1/system-admin/schools/?county=kiambu')
        data = response.data['data']
        assert data['total'] == 1
        assert data['results'][0]['county'] == 'kiambu'

    def test_search_by_name(self):
        SchoolFactory(name='Starehe Boys')
        SchoolFactory(name='Alliance Girls')
        response = self.client.get('/api/v1/system-admin/schools/?search=starehe')
        data = response.data['data']
        assert data['total'] == 1

    def test_search_by_school_code(self):
        SchoolFactory(school_code='NAI001')
        SchoolFactory(school_code='KIA002')
        response = self.client.get('/api/v1/system-admin/schools/?search=NAI')
        data = response.data['data']
        assert data['total'] == 1

    def test_filter_active_only(self):
        SchoolFactory(is_active=True)
        SchoolFactory(is_active=False)
        response = self.client.get('/api/v1/system-admin/schools/?active=true')
        assert response.data['data']['total'] == 1

    def test_pagination(self):
        for i in range(25):
            SchoolFactory()
        response = self.client.get('/api/v1/system-admin/schools/?page=2')
        data = response.data['data']
        assert data['total'] == 25
        assert data['page'] == 2
        assert len(data['results']) == 5

    def test_includes_student_and_counselor_counts(self):
        school = SchoolFactory()
        CounselorFactory(school=school)
        StudentProfileFactory(school=school, mode='school_linked')
        response = self.client.get('/api/v1/system-admin/schools/')
        result = response.data['data']['results'][0]
        assert result['student_count'] == 1
        assert result['counselor_count'] == 1

    def test_create_school(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'New School',
            'county': 'kiambu',
            'school_code': 'KIA999',
        })
        assert response.status_code == 201
        data = response.data['data']
        assert data['name'] == 'New School'
        assert data['county'] == 'kiambu'
        assert data['school_code'] == 'KIA999'
        assert data['is_active'] is True
        assert AuditLog.objects.filter(action='school_created').count() == 1

    def test_create_school_duplicate_code(self):
        SchoolFactory(school_code='DUP001')
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'Another School',
            'county': 'kiambu',
            'school_code': 'DUP001',
        })
        assert response.status_code == 400

    def test_create_school_invalid_county(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'Bad County School',
            'county': 'mombasa',
            'school_code': 'BAD001',
        })
        assert response.status_code == 400

    def test_create_school_missing_name(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'county': 'kiambu',
            'school_code': 'MISS01',
        })
        assert response.status_code == 400

    def test_requires_system_admin(self):
        client = APIClient()
        client.force_authenticate(SchoolAdminFactory())
        response = client.get('/api/v1/system-admin/schools/')
        assert response.status_code == 403


class TestSchoolDetailView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)
        self.school = SchoolFactory(name='Test School', county='kiambu', school_code='TST001')

    def test_get_school_detail(self):
        response = self.client.get(f'/api/v1/system-admin/schools/{self.school.id}/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['name'] == 'Test School'
        assert 'counselors' in data
        assert 'recent_students' in data

    def test_get_nonexistent_school(self):
        response = self.client.get('/api/v1/system-admin/schools/99999/')
        assert response.status_code == 404

    def test_patch_school(self):
        response = self.client.patch(f'/api/v1/system-admin/schools/{self.school.id}/', {
            'name': 'Updated School',
            'phone': '+254700000000',
        })
        assert response.status_code == 200
        assert response.data['data']['name'] == 'Updated School'
        assert response.data['data']['phone'] == '+254700000000'
        assert AuditLog.objects.filter(action='school_edited').count() == 1

    def test_patch_rejects_non_string(self):
        response = self.client.patch(
            f'/api/v1/system-admin/schools/{self.school.id}/',
            {'name': 123},
            format='json',
        )
        assert response.status_code == 400

    def test_patch_no_valid_fields(self):
        response = self.client.patch(f'/api/v1/system-admin/schools/{self.school.id}/', {
            'county': 'nyeri',
        })
        assert response.status_code == 400

    def test_patch_validates_email(self):
        response = self.client.patch(f'/api/v1/system-admin/schools/{self.school.id}/', {
            'email': 'not-an-email',
        })
        assert response.status_code == 400


class TestSchoolDeactivateActivate:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)
        self.school = SchoolFactory()

    def test_deactivate_school(self):
        response = self.client.post(f'/api/v1/system-admin/schools/{self.school.id}/deactivate/')
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.is_active is False
        assert AuditLog.objects.filter(action='school_deactivated').count() == 1

    def test_deactivate_already_inactive(self):
        self.school.is_active = False
        self.school.save(update_fields=['is_active'])
        response = self.client.post(f'/api/v1/system-admin/schools/{self.school.id}/deactivate/')
        assert response.status_code == 400

    def test_activate_school(self):
        self.school.is_active = False
        self.school.save(update_fields=['is_active'])
        response = self.client.post(f'/api/v1/system-admin/schools/{self.school.id}/activate/')
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.is_active is True
        assert AuditLog.objects.filter(action='school_activated').count() == 1

    def test_activate_already_active(self):
        response = self.client.post(f'/api/v1/system-admin/schools/{self.school.id}/activate/')
        assert response.status_code == 400

    def test_deactivate_nonexistent(self):
        response = self.client.post('/api/v1/system-admin/schools/99999/deactivate/')
        assert response.status_code == 404
