import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient
from tests.factories import (
    AssessmentFrameworkFactory,
    AuditLogFactory,
    CounselorAssignmentFactory,
    CounselorFactory,
    FrameworkVersionFactory,
    InstitutionFactory,
    ProgrammeFactory,
    PerformanceLevelDefinitionFactory,
    SchoolAdminFactory,
    SchoolFactory,
    StudentProfileFactory,
    SubjectCombinationFactory,
    SystemAdminFactory,
    VerifiedUserFactory,
)
from students.models import AssessmentFramework
from system_admin.models import AuditLog
from accounts.models import School, StudentProfile
from guidance.models import LearnerCombinationChoice, LearnerPlan

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestDashboardView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)
        self.base_active_schools = School.objects.filter(is_active=True).count()
        self.base_registered_learners = StudentProfile.objects.count()
        self.base_verified_learners = StudentProfile.objects.filter(
            user__is_email_verified=True,
        ).count()
        self.base_pending_links = StudentProfile.objects.filter(
            school_membership_status='pending',
        ).count()
        self.base_completed_plans = LearnerPlan.objects.filter(
            review_status='reviewed',
        ).count()

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
        assert data['total_schools'] == self.base_active_schools + 2
        assert 'recent_signups' in data
        assert 'recent_audit' in data
        assert 'learners_by_county' in data
        assert 'verified_learners' in data
        assert 'pending_school_links' in data
        assert 'assignment_coverage' in data
        assert 'plans_completed' in data
        assert 'framework' in data

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
        assert (
            response.data['data']['total_schools']
            == self.base_active_schools + 1
        )

    def test_dashboard_reports_real_pilot_health(self):
        school = SchoolFactory(county='kiambu', is_active=True)
        assigned = StudentProfileFactory(
            user__county='kiambu',
            user__is_email_verified=True,
            school=school,
            mode='school_linked',
            school_membership_status='active',
        )
        StudentProfileFactory(
            user__county='nyeri',
            user__is_email_verified=False,
            school=SchoolFactory(county='nyeri'),
            mode='school_linked',
            school_membership_status='pending',
        )
        counselor = CounselorFactory(school=school)
        CounselorAssignmentFactory(
            counselor=counselor,
            student_profile=assigned,
            school=school,
        )
        framework = FrameworkVersionFactory(is_active=True)
        combination = SubjectCombinationFactory(
            framework_version=framework,
            track__framework_version=framework,
        )
        choice = LearnerCombinationChoice.objects.create(
            student_profile=assigned,
            combination=combination,
            status='provisional',
        )
        LearnerPlan.objects.create(
            student_profile=assigned,
            provisional_choice=choice,
            review_status='reviewed',
        )

        response = self.client.get('/api/v1/system-admin/dashboard/')

        assert response.status_code == 200
        data = response.data['data']
        assert data['registered_learners'] == self.base_registered_learners + 2
        assert data['learners_by_county']['kiambu'] >= 1
        assert data['learners_by_county']['nyeri'] >= 1
        assert data['verified_learners'] == self.base_verified_learners + 1
        assert data['pending_school_links'] == self.base_pending_links + 1
        assert data['assignment_coverage'] == {
            'assigned': 1,
            'eligible': 1,
            'percent': 100,
        }
        assert data['plans_completed'] == self.base_completed_plans + 1
        assert data['framework']['code'] == framework.code
        assert data['framework']['effective_date'] == framework.effective_date.isoformat()
        assert data['framework']['source_url'] == framework.source_url


class TestFrameworkCatalogueView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)
        self.framework = FrameworkVersionFactory(is_active=True)
        self.active_combination = SubjectCombinationFactory(
            framework_version=self.framework,
            track__framework_version=self.framework,
            is_active=True,
        )
        self.inactive_combination = SubjectCombinationFactory(
            framework_version=self.framework,
            track__framework_version=self.framework,
            is_active=False,
        )

    def test_lists_current_framework_and_all_its_combinations(self):
        response = self.client.get('/api/v1/system-admin/catalogue/')

        assert response.status_code == 200
        data = response.data['data']
        assert data['framework']['id'] == self.framework.id
        assert data['framework']['source_url'] == self.framework.source_url
        assert data['framework']['effective_date'] == str(
            self.framework.effective_date
        )
        combinations = {
            item['id']: item for item in data['combinations']
        }
        assert combinations[self.active_combination.id]['is_active'] is True
        assert combinations[self.inactive_combination.id]['is_active'] is False
        assert len(combinations[self.active_combination.id]['subjects']) == 3

    def test_list_only_includes_current_framework(self):
        old_framework = FrameworkVersionFactory(is_active=False)
        old_combination = SubjectCombinationFactory(
            framework_version=old_framework,
            track__framework_version=old_framework,
        )

        response = self.client.get('/api/v1/system-admin/catalogue/')

        ids = {
            item['id'] for item in response.data['data']['combinations']
        }
        assert old_combination.id not in ids

    def test_update_combination_status_and_audit(self):
        response = self.client.patch(
            (
                '/api/v1/system-admin/catalogue/combinations/'
                f'{self.active_combination.id}/'
            ),
            {'is_active': False},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['data']['is_active'] is False
        self.active_combination.refresh_from_db()
        assert self.active_combination.is_active is False
        entry = AuditLog.objects.get(
            action='framework_combination_status_changed'
        )
        assert entry.target_type == 'combination'
        assert entry.target_id == self.active_combination.id
        assert entry.details['previous_is_active'] is True
        assert entry.details['is_active'] is False

    @pytest.mark.parametrize('value', ['false', 0, None])
    def test_update_rejects_non_boolean_status(self, value):
        response = self.client.patch(
            (
                '/api/v1/system-admin/catalogue/combinations/'
                f'{self.active_combination.id}/'
            ),
            {'is_active': value},
            format='json',
        )

        assert response.status_code == 400

    def test_update_rejects_combination_from_old_framework(self):
        old_framework = FrameworkVersionFactory(is_active=False)
        old_combination = SubjectCombinationFactory(
            framework_version=old_framework,
            track__framework_version=old_framework,
        )

        response = self.client.patch(
            (
                '/api/v1/system-admin/catalogue/combinations/'
                f'{old_combination.id}/'
            ),
            {'is_active': False},
            format='json',
        )

        assert response.status_code == 404

    def test_requires_system_admin(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='student'))

        response = client.get('/api/v1/system-admin/catalogue/')

        assert response.status_code == 403


class TestAcademicSourceMetadataView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_lists_assessment_and_tertiary_provenance(self):
        framework = AssessmentFrameworkFactory(
            status=AssessmentFramework.STATUS_DRAFT,
        )
        institution = InstitutionFactory()
        programme = ProgrammeFactory(institution=institution)

        response = self.client.get('/api/v1/system-admin/source-metadata/')

        assert response.status_code == 200
        data = response.data['data']
        assessment = next(
            item for item in data['assessment_frameworks']
            if item['id'] == framework.id
        )
        assert assessment['version'] == framework.version
        assert assessment['source_url'] == framework.source_url
        assert assessment['effective_date'] == framework.effective_date.isoformat()
        sources = {
            (item['record_type'], item['id']): item
            for item in data['tertiary_sources']
        }
        assert sources[('institution', institution.id)]['admission_cycle'] == '2025/2026'
        assert sources[('institution', institution.id)]['can_change_status'] is False
        assert sources[('programme', programme.id)]['education_framework'] == 'KCSE'

    def test_changes_unreferenced_tertiary_status_and_audits(self):
        institution = InstitutionFactory()

        response = self.client.patch(
            f'/api/v1/system-admin/source-metadata/institution/{institution.id}/',
            {'status': 'unavailable'},
            format='json',
        )

        assert response.status_code == 200
        institution.refresh_from_db()
        assert institution.verification_status == 'unavailable'
        entry = AuditLog.objects.get(action='tertiary_source_status_changed')
        assert entry.details['previous_status'] == 'historical'
        assert entry.details['status'] == 'unavailable'

    def test_rejects_status_change_once_tertiary_source_is_referenced(self):
        institution = InstitutionFactory()
        ProgrammeFactory(institution=institution)

        response = self.client.patch(
            f'/api/v1/system-admin/source-metadata/institution/{institution.id}/',
            {'status': 'unavailable'},
            format='json',
        )

        assert response.status_code == 409
        institution.refresh_from_db()
        assert institution.verification_status == 'historical'

    def test_changes_assessment_framework_lifecycle_and_audits(self):
        framework = AssessmentFrameworkFactory(
            status=AssessmentFramework.STATUS_DRAFT,
        )

        response = self.client.patch(
            f'/api/v1/system-admin/source-metadata/assessment_framework/{framework.id}/',
            {'status': 'retired'},
            format='json',
        )

        assert response.status_code == 200
        framework.refresh_from_db()
        assert framework.status == AssessmentFramework.STATUS_RETIRED
        assert AuditLog.objects.filter(
            action='assessment_framework_status_changed',
            target_id=framework.id,
        ).exists()

    def test_reactivates_retired_assessment_framework(self):
        framework = AssessmentFrameworkFactory(
            status=AssessmentFramework.STATUS_RETIRED,
        )
        for code, rank in (
            ('EE1', 8), ('EE2', 7), ('ME1', 6), ('ME2', 5),
            ('AE1', 4), ('AE2', 3), ('BE1', 2), ('BE2', 1),
        ):
            PerformanceLevelDefinitionFactory(
                framework=framework,
                code=code,
                rank=rank,
            )

        response = self.client.patch(
            f'/api/v1/system-admin/source-metadata/assessment_framework/{framework.id}/',
            {'status': 'active'},
            format='json',
        )

        assert response.status_code == 200
        framework.refresh_from_db()
        assert framework.status == AssessmentFramework.STATUS_ACTIVE
        entry = AuditLog.objects.get(
            action='assessment_framework_status_changed',
            target_id=framework.id,
        )
        assert entry.details['previous_status'] == 'retired'
        assert entry.details['status'] == 'active'

    def test_rejects_activation_until_all_cbe_levels_and_ranks_exist(self):
        framework = AssessmentFrameworkFactory(
            status=AssessmentFramework.STATUS_DRAFT,
        )
        PerformanceLevelDefinitionFactory(
            framework=framework,
            code='EE1',
            rank=8,
        )

        response = self.client.patch(
            f'/api/v1/system-admin/source-metadata/assessment_framework/{framework.id}/',
            {'status': 'active'},
            format='json',
        )

        assert response.status_code == 400
        assert 'EE1–BE2' in str(response.data['message'])
        framework.refresh_from_db()
        assert framework.status == AssessmentFramework.STATUS_DRAFT

    def test_metadata_queries_stay_bounded_as_source_records_grow(self):
        for _index in range(5):
            AssessmentFrameworkFactory()
            institution = InstitutionFactory()
            ProgrammeFactory(institution=institution)

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get('/api/v1/system-admin/source-metadata/')

        assert response.status_code == 200
        assert len(response.data['data']['assessment_frameworks']) >= 5
        assert len(response.data['data']['tertiary_sources']) >= 10
        assert len(captured) <= 3

    def test_source_metadata_requires_system_admin(self):
        client = APIClient()
        client.force_authenticate(VerifiedUserFactory(role='student'))

        response = client.get('/api/v1/system-admin/source-metadata/')

        assert response.status_code == 403


class TestSchoolListView:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)
        self.base_school_count = School.objects.count()
        self.base_active_school_count = School.objects.filter(
            is_active=True,
        ).count()
        self.base_county_counts = {
            county: School.objects.filter(county=county).count()
            for county in ('kiambu', 'nyeri')
        }

    def test_list_all_schools(self):
        SchoolFactory(name='Alpha School')
        SchoolFactory(name='Beta School')
        response = self.client.get('/api/v1/system-admin/schools/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['total'] == self.base_school_count + 2
        assert len(data['results']) == self.base_school_count + 2

    def test_filter_by_county(self):
        SchoolFactory(county='kiambu')
        SchoolFactory(county='nyeri')
        response = self.client.get('/api/v1/system-admin/schools/?county=kiambu')
        data = response.data['data']
        assert data['total'] == self.base_county_counts['kiambu'] + 1
        assert all(result['county'] == 'kiambu' for result in data['results'])

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
        assert (
            response.data['data']['total']
            == self.base_active_school_count + 1
        )

    def test_pagination(self):
        for i in range(25):
            SchoolFactory()
        response = self.client.get('/api/v1/system-admin/schools/?page=2')
        data = response.data['data']
        assert data['total'] == self.base_school_count + 25
        assert data['page'] == 2
        assert len(data['results']) == min(
            20,
            self.base_school_count + 25 - 20,
        )

    def test_includes_student_and_counselor_counts(self):
        school = SchoolFactory()
        CounselorFactory(school=school)
        StudentProfileFactory(school=school, mode='school_linked')
        response = self.client.get('/api/v1/system-admin/schools/')
        result = next(
            item
            for item in response.data['data']['results']
            if item['id'] == school.id
        )
        assert result['student_count'] == 1
        assert result['counselor_count'] == 1

    def test_create_school(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'New School',
            'county': 'kiambu',
            'school_code': 'KIA999',
            'email': 'admin@newschool.ac.ke',
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
            'email': 'admin@another.ac.ke',
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
        StudentProfileFactory(user=student, grade=9, mode='self_guided')
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
        response = self.client.get(
            '/api/v1/system-admin/audit-logs/?date_from=2026-01-01&date_to=2026-12-31')
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


class TestInputValidation:
    """Verify invalid query params return 200 (not 500)."""

    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_users_invalid_school_param(self):
        response = self.client.get('/api/v1/system-admin/users/?school=abc')
        assert response.status_code == 200

    def test_audit_logs_invalid_actor_param(self):
        response = self.client.get('/api/v1/system-admin/audit-logs/?actor=abc')
        assert response.status_code == 200

    def test_audit_logs_invalid_date_from(self):
        response = self.client.get('/api/v1/system-admin/audit-logs/?date_from=not-a-date')
        assert response.status_code == 200

    def test_audit_logs_invalid_date_to(self):
        response = self.client.get('/api/v1/system-admin/audit-logs/?date_to=xyz')
        assert response.status_code == 200

    def test_audit_logs_valid_dates_still_filter(self):
        AuditLogFactory(actor=self.admin, action='school_created', target_id=1)
        response = self.client.get(
            '/api/v1/system-admin/audit-logs/?date_from=2026-01-01&date_to=2026-12-31')
        assert response.status_code == 200
        assert response.data['data']['total'] >= 1

    def test_create_school_invalid_email_rejected(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'Bad Email School',
            'county': 'kiambu',
            'school_code': 'BAD001',
            'email': 'not-an-email',
        }, format='json')
        assert response.status_code == 400

    def test_create_school_empty_email_rejected(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'No Email School',
            'county': 'kiambu',
            'school_code': 'NOEML01',
        }, format='json')
        assert response.status_code == 400

    def test_create_school_valid_email_accepted(self):
        response = self.client.post('/api/v1/system-admin/schools/', {
            'name': 'Valid Email School',
            'county': 'nyeri',
            'school_code': 'VALID01',
            'email': 'school@example.com',
        }, format='json')
        assert response.status_code == 201


@pytest.fixture
def client():
    return APIClient()


class TestSchoolCreationProvisionsAdmin:
    def setup_method(self):
        self.admin = SystemAdminFactory()

    def test_create_school_without_email_fails(self, client):
        client.force_authenticate(self.admin)
        response = client.post('/api/v1/system-admin/schools/', {
            'name': 'Kilimani Girls', 'county': 'kiambu', 'school_code': 'KIL-001',
        }, format='json')
        assert response.status_code == 400

    def test_create_school_with_taken_email_fails(self, client):
        client.force_authenticate(self.admin)
        User.objects.create_user(
            email='taken@kilimani.ac.ke', password='TestPass123!', role='counselor', county='kiambu',
        )
        response = client.post('/api/v1/system-admin/schools/', {
            'name': 'Kilimani Girls', 'county': 'kiambu', 'school_code': 'KIL-002',
            'email': 'taken@kilimani.ac.ke',
        }, format='json')
        assert response.status_code == 400
        assert 'already exists' in str(response.data['message'])

    def test_create_school_provisions_admin_account(self, client, mailoutbox):
        client.force_authenticate(self.admin)
        response = client.post('/api/v1/system-admin/schools/', {
            'name': 'Kilimani Girls', 'county': 'kiambu', 'school_code': 'KIL-003',
            'email': 'admin@kilimani.ac.ke',
        }, format='json')
        assert response.status_code == 201
        school = School.objects.get(school_code='KIL-003')
        user = User.objects.get(email='admin@kilimani.ac.ke')
        assert user.role == 'school_admin'
        assert user.school == school
        assert user.is_email_verified is True
        assert user.first_name == 'Kilimani Girls'
        assert user.last_name == 'Administrator'
        assert len(mailoutbox) == 1
        assert 'admin@kilimani.ac.ke' in mailoutbox[0].to
        assert user.check_password(_extract_temp_password(mailoutbox[0].body))


def _extract_temp_password(email_body):
    for line in email_body.splitlines():
        if line.strip() and not line.startswith(('Hi', 'A new', 'This', 'You can')):
            candidate = line.strip()
            if len(candidate) >= 8:
                return candidate
    raise AssertionError('Could not find temp password in email body')
