import pytest
from rest_framework.test import APIClient

from system_admin.models import AuditLog
from tests.factories import (
    CounselorAssignmentFactory,
    CounselorFactory,
    SchoolAdminFactory,
    SchoolFactory,
    StudentProfileFactory,
    SystemAdminFactory,
)

pytestmark = pytest.mark.django_db


def _fake_pdf(_data):
    return b'%PDF-1.4 test'


class TestSchoolReports:
    def setup_method(self):
        self.client = APIClient()
        self.school = SchoolFactory(name='Scope School')
        self.admin = SchoolAdminFactory(school=self.school)
        self.client.force_authenticate(self.admin)

    def test_overview_downloads_and_audits(self, monkeypatch):
        monkeypatch.setattr('reports.views.build_cohort_overview_report', _fake_pdf)
        response = self.client.get('/api/v1/reports/school/overview/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        log = AuditLog.objects.get(action='report_downloaded')
        assert log.details['report_type'] == 'school_overview'
        assert log.target_id == self.school.id

    def test_roster_is_scoped_and_filtered_by_grade(self, monkeypatch):
        included = StudentProfileFactory(
            school=self.school, mode='school_linked',
            school_membership_status='active', grade=10,
        )
        StudentProfileFactory(
            school=self.school, mode='school_linked',
            school_membership_status='active', grade=9,
        )
        StudentProfileFactory(
            school=SchoolFactory(), mode='school_linked',
            school_membership_status='active', grade=10,
        )
        captured = {}
        monkeypatch.setattr(
            'reports.views.build_cohort_roster_report',
            lambda data: captured.update(data) or b'%PDF test',
        )
        response = self.client.get('/api/v1/reports/school/roster/pdf/?grade=10')
        assert response.status_code == 200
        assert [row['name'] for row in captured['rows']] == [
            f'{included.user.first_name} {included.user.last_name}'.strip(),
        ]
        assert captured['include_counselor'] is True

    @pytest.mark.parametrize('grade', ['8', '13', 'ME1', 'ten'])
    def test_roster_rejects_invalid_grade(self, grade):
        response = self.client.get(f'/api/v1/reports/school/roster/pdf/?grade={grade}')
        assert response.status_code == 400
        assert response.data['message'] == 'Invalid grade filter.'

    def test_wrong_role_is_forbidden(self):
        self.client.force_authenticate(CounselorFactory())
        response = self.client.get('/api/v1/reports/school/overview/pdf/')
        assert response.status_code == 403

    def test_admin_without_school_gets_404(self):
        self.client.force_authenticate(SchoolAdminFactory(school=None))
        response = self.client.get('/api/v1/reports/school/overview/pdf/')
        assert response.status_code == 404


class TestCounselorReports:
    def setup_method(self):
        self.client = APIClient()
        self.counselor = CounselorFactory()
        self.client.force_authenticate(self.counselor)

    def test_overview_downloads_and_audits(self, monkeypatch):
        monkeypatch.setattr('reports.views.build_cohort_overview_report', _fake_pdf)
        response = self.client.get('/api/v1/reports/counselor/overview/pdf/')
        assert response.status_code == 200
        log = AuditLog.objects.get(action='report_downloaded')
        assert log.details['report_type'] == 'counselor_overview'

    def test_roster_contains_only_active_assignments(self, monkeypatch):
        included = StudentProfileFactory(grade=10)
        CounselorAssignmentFactory(
            counselor=self.counselor, student_profile=included,
            school=SchoolFactory(), is_active=True,
        )
        excluded = StudentProfileFactory(grade=10)
        CounselorAssignmentFactory(
            counselor=CounselorFactory(), student_profile=excluded,
            school=SchoolFactory(), is_active=True,
        )
        captured = {}
        monkeypatch.setattr(
            'reports.views.build_cohort_roster_report',
            lambda data: captured.update(data) or b'%PDF test',
        )
        response = self.client.get('/api/v1/reports/counselor/roster/pdf/?grade=10')
        assert response.status_code == 200
        assert len(captured['rows']) == 1
        assert captured['rows'][0]['name'] == (
            f'{included.user.first_name} {included.user.last_name}'.strip()
        )
        assert captured['include_counselor'] is False

    def test_roster_empty_result_is_valid(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            'reports.views.build_cohort_roster_report',
            lambda data: captured.update(data) or b'%PDF test',
        )
        response = self.client.get('/api/v1/reports/counselor/roster/pdf/?grade=12')
        assert response.status_code == 200
        assert captured['rows'] == []

    def test_wrong_role_is_forbidden(self):
        self.client.force_authenticate(SystemAdminFactory())
        response = self.client.get('/api/v1/reports/counselor/overview/pdf/')
        assert response.status_code == 403


class TestSystemReports:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_platform_overview_downloads_and_audits(self, monkeypatch):
        monkeypatch.setattr('reports.views.build_platform_overview_report', _fake_pdf)
        response = self.client.get('/api/v1/reports/system/overview/pdf/')
        assert response.status_code == 200
        assert AuditLog.objects.get(action='report_downloaded').details['report_type'] == 'system_overview'

    def test_schools_directory_passes_annotated_counts(self, monkeypatch):
        school = SchoolFactory(name='Directory School')
        StudentProfileFactory(
            school=school, mode='school_linked',
            school_membership_status='active',
        )
        CounselorFactory(school=school)
        captured = {}
        monkeypatch.setattr(
            'reports.views.build_schools_directory_report',
            lambda data: captured.update(data) or b'%PDF test',
        )
        response = self.client.get('/api/v1/reports/system/schools/pdf/')
        assert response.status_code == 200
        row = next(item for item in captured['schools'] if item['id'] == school.id)
        assert row['student_count'] == 1
        assert row['counselor_count'] == 1

    def test_wrong_role_is_forbidden(self):
        self.client.force_authenticate(SchoolAdminFactory())
        response = self.client.get('/api/v1/reports/system/overview/pdf/')
        assert response.status_code == 403
