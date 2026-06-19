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


class TestUserListView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_list_all_users(self):
        VerifiedUserFactory(role='student')
        VerifiedUserFactory(role='counselor')
        response = self.client.get('/api/v1/system-admin/users/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['total'] >= 3  # 2 created + the admin itself

    def test_filter_by_role(self):
        VerifiedUserFactory(role='student')
        VerifiedUserFactory(role='counselor')
        response = self.client.get('/api/v1/system-admin/users/?role=student')
        data = response.data['data']
        for u in data['results']:
            assert u['role'] == 'student'

    def test_filter_by_county(self):
        VerifiedUserFactory(role='student', county='nyeri')
        VerifiedUserFactory(role='student', county='kiambu')
        response = self.client.get('/api/v1/system-admin/users/?county=nyeri')
        data = response.data['data']
        for u in data['results']:
            assert u['county'] == 'nyeri'

    def test_search_by_email(self):
        VerifiedUserFactory(email='unique_test_email@example.com', role='student')
        response = self.client.get('/api/v1/system-admin/users/?search=unique_test_email')
        data = response.data['data']
        assert data['total'] == 1

    def test_filter_active(self):
        u = VerifiedUserFactory(role='student')
        u.is_active = False
        u.save(update_fields=['is_active'])
        response = self.client.get('/api/v1/system-admin/users/?active=false')
        data = response.data['data']
        assert data['total'] == 1

    def test_pagination(self):
        for _ in range(25):
            VerifiedUserFactory(role='student')
        response = self.client.get('/api/v1/system-admin/users/?page=2')
        data = response.data['data']
        assert data['page'] == 2

    def test_includes_school_name(self):
        school = SchoolFactory(name='My School')
        VerifiedUserFactory(role='counselor', school=school)
        response = self.client.get('/api/v1/system-admin/users/?role=counselor')
        results = response.data['data']['results']
        counselor = next(r for r in results if r['school_name'] == 'My School')
        assert counselor['school_name'] == 'My School'

    def test_requires_system_admin(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='student'))
        response = client.get('/api/v1/system-admin/users/')
        assert response.status_code == 403


class TestUserDetailView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_get_student_detail(self):
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9, mode='self_guided')
        response = self.client.get(f'/api/v1/system-admin/users/{student.id}/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['email'] == student.email
        assert data['grade'] == 9
        assert data['mode'] == 'self_guided'
        assert data['has_assessment'] is False

    def test_get_counselor_detail(self):
        counselor = CounselorFactory()
        response = self.client.get(f'/api/v1/system-admin/users/{counselor.id}/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['role'] == 'counselor'
        assert data['student_count'] == 0

    def test_nonexistent_user(self):
        response = self.client.get('/api/v1/system-admin/users/99999/')
        assert response.status_code == 404


class TestUserDeactivateActivate:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_deactivate_user(self):
        user = VerifiedUserFactory(role='student')
        response = self.client.post(f'/api/v1/system-admin/users/{user.id}/deactivate/')
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_active is False
        assert AuditLog.objects.filter(action='account_deactivated').count() == 1

    def test_cannot_deactivate_self(self):
        response = self.client.post(f'/api/v1/system-admin/users/{self.admin.id}/deactivate/')
        assert response.status_code == 400

    def test_deactivate_already_inactive(self):
        user = VerifiedUserFactory(role='student')
        user.is_active = False
        user.save(update_fields=['is_active'])
        response = self.client.post(f'/api/v1/system-admin/users/{user.id}/deactivate/')
        assert response.status_code == 400

    def test_activate_user(self):
        user = VerifiedUserFactory(role='student')
        user.is_active = False
        user.save(update_fields=['is_active'])
        response = self.client.post(f'/api/v1/system-admin/users/{user.id}/activate/')
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_active is True
        assert AuditLog.objects.filter(action='account_activated').count() == 1

    def test_activate_already_active(self):
        user = VerifiedUserFactory(role='student')
        response = self.client.post(f'/api/v1/system-admin/users/{user.id}/activate/')
        assert response.status_code == 400

    def test_deactivate_nonexistent(self):
        response = self.client.post('/api/v1/system-admin/users/99999/deactivate/')
        assert response.status_code == 404


class TestAuditLogListView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_list_audit_logs(self):
        AuditLogFactory(actor=self.admin, action='school_created', target_id=1)
        AuditLogFactory(actor=self.admin, action='invite_sent', target_id=2)
        response = self.client.get('/api/v1/system-admin/audit-logs/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['total'] == 2

    def test_filter_by_action(self):
        AuditLogFactory(action='school_created')
        AuditLogFactory(action='invite_sent')
        response = self.client.get('/api/v1/system-admin/audit-logs/?action=school_created')
        data = response.data['data']
        assert data['total'] == 1
        assert data['results'][0]['action'] == 'school_created'

    def test_filter_by_date_range(self):
        AuditLogFactory(action='school_created')
        response = self.client.get('/api/v1/system-admin/audit-logs/?date_from=2026-01-01&date_to=2026-12-31')
        data = response.data['data']
        assert data['total'] >= 1

    def test_pagination(self):
        for i in range(25):
            AuditLogFactory(target_id=i)
        response = self.client.get('/api/v1/system-admin/audit-logs/?page=2')
        data = response.data['data']
        assert data['page'] == 2
        assert len(data['results']) == 5

    def test_requires_system_admin(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='student'))
        response = client.get('/api/v1/system-admin/audit-logs/')
        assert response.status_code == 403


class TestAuditLogIntegration:
    """Verify audit log entries are created by existing views."""

    def setup_method(self):
        self.client = APIClient()

    def test_registration_creates_audit_log(self):
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'newstudent@test.com',
            'password': 'TestPass123!',
            'first_name': 'New',
            'last_name': 'Student',
            'role': 'student',
            'county': 'kiambu',
            'grade': 9,
        }, format='json')
        assert response.status_code == 201
        assert AuditLog.objects.filter(action='user_registered').count() == 1

    def test_invite_sent_creates_audit_log(self):
        admin = SystemAdminFactory()
        self.client.force_authenticate(admin)
        response = self.client.post('/api/v1/auth/invite/', {
            'email': 'newcounselor@test.com',
            'role': 'counselor',
        })
        assert response.status_code == 200
        entry = AuditLog.objects.get(action='invite_sent')
        assert entry.details['email'] == 'newcounselor@test.com'
        assert entry.details['role'] == 'counselor'

    def test_counselor_add_creates_audit_log(self):
        school = SchoolFactory()
        school_admin = SchoolAdminFactory(school=school)
        counselor = CounselorFactory(school=None)
        self.client.force_authenticate(school_admin)
        response = self.client.post('/api/v1/school-admin/counselors/add/', {
            'email': counselor.email,
        })
        assert response.status_code == 200
        assert AuditLog.objects.filter(action='counselor_added').count() == 1

    def test_counselor_remove_creates_audit_log(self):
        school = SchoolFactory()
        school_admin = SchoolAdminFactory(school=school)
        counselor = CounselorFactory(school=school)
        self.client.force_authenticate(school_admin)
        response = self.client.post(f'/api/v1/school-admin/counselors/{counselor.id}/remove/')
        assert response.status_code == 200
        assert AuditLog.objects.filter(action='counselor_removed').count() == 1
