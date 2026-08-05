from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from students.models import CBCGrade
from system_admin.models import AuditLog
from tests.factories import (
    AcademicPeriodFactory,
    SchoolAdminFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db


def learner_client(profile):
    client = APIClient()
    client.force_authenticate(profile.user)
    return client


class TestLearnerAcademicPeriodRules:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student')
        )
        self.enrollment = StudentSubjectFactory(student_profile=self.profile)
        self.url = (
            f'/api/v1/students/my-subjects/{self.enrollment.id}/grades/'
        )
        self.client = learner_client(self.profile)

    def test_unfinished_term_cannot_receive_marks(self):
        now = timezone.now()
        AcademicPeriodFactory(
            year=2026,
            term=1,
            term_ends_at=now + timedelta(days=2),
            entry_opens_at=now + timedelta(days=2),
            entry_closes_at=now + timedelta(days=9),
        )

        response = self.client.post(
            self.url,
            {'year': 2026, 'term': 1, 'level': 'ME1'},
            format='json',
        )

        assert response.status_code == 409
        assert 'not open' in response.data['message'].lower()
        assert CBCGrade.objects.count() == 0

    def test_open_term_accepts_learner_marks(self):
        AcademicPeriodFactory(year=2026, term=1)

        response = self.client.post(
            self.url,
            {'year': 2026, 'term': 1, 'level': 'ME1'},
            format='json',
        )

        assert response.status_code == 201
        assert response.data['data']['source'] == 'learner'

    def test_closed_term_cannot_be_edited_or_deleted(self):
        now = timezone.now()
        AcademicPeriodFactory(
            year=2026,
            term=1,
            term_ends_at=now - timedelta(days=10),
            entry_opens_at=now - timedelta(days=9),
            entry_closes_at=now - timedelta(days=1),
        )
        grade = CBCGrade.objects.create(
            student_subject=self.enrollment,
            year=2026,
            term=1,
            level='ME1',
        )
        detail_url = f'{self.url}{grade.id}/'

        updated = self.client.put(
            detail_url,
            {'year': 2026, 'term': 1, 'level': 'EE1'},
            format='json',
        )
        deleted = self.client.delete(detail_url)

        assert updated.status_code == 409
        assert deleted.status_code == 409
        grade.refresh_from_db()
        assert grade.level == 'ME1'

    def test_period_endpoint_reports_availability(self):
        AcademicPeriodFactory(year=2026, term=1)

        response = self.client.get('/api/v1/students/academic-periods/')

        assert response.status_code == 200
        assert response.data['data'][0]['state'] == 'entry_open'
        assert response.data['data'][0]['can_submit'] is True


class TestSchoolMarksUpload:
    def setup_method(self):
        self.admin = SchoolAdminFactory()
        self.profile = StudentProfileFactory(
            school=self.admin.school,
            mode='school_linked',
            school_membership_status='active',
        )
        self.enrollment = StudentSubjectFactory(student_profile=self.profile)
        self.period = AcademicPeriodFactory(year=2026, term=1)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def upload(self, *, preview):
        content = (
            'student_email,subject_code,level,raw_score\n'
            f'{self.profile.user.email},{self.enrollment.subject.code},EE1,87.5\n'
        ).encode()
        file = SimpleUploadedFile('marks.csv', content, content_type='text/csv')
        return self.client.post(
            '/api/v1/school-admin/marks/import/',
            {
                'period_id': str(self.period.id),
                'preview': 'true' if preview else 'false',
                'file': file,
            },
            format='multipart',
        )

    def test_preview_validates_without_writing(self):
        response = self.upload(preview=True)

        assert response.status_code == 200
        assert response.data['data']['valid_count'] == 1
        assert response.data['data']['rows'][0]['action'] == 'create'
        assert CBCGrade.objects.count() == 0

    def test_commit_creates_verified_school_evidence_and_audit(self):
        response = self.upload(preview=False)

        assert response.status_code == 201
        grade = CBCGrade.objects.get()
        assert grade.source == 'school'
        assert grade.level == 'EE1'
        assert grade.raw_score == pytest.approx(87.5)
        assert grade.verified_by == self.admin
        assert grade.verified_school == self.admin.school
        assert AuditLog.objects.filter(
            action='school_marks_imported',
            target_id=self.period.id,
        ).exists()

    def test_upload_is_rejected_before_term_completion(self):
        now = timezone.now()
        self.period.term_ends_at = now + timedelta(days=2)
        self.period.entry_opens_at = now + timedelta(days=2)
        self.period.entry_closes_at = now + timedelta(days=5)
        self.period.save()

        response = self.upload(preview=False)

        assert response.status_code == 409
        assert CBCGrade.objects.count() == 0

    def test_invalid_row_prevents_partial_commit(self):
        content = (
            'student_email,subject_code,level\n'
            f'{self.profile.user.email},{self.enrollment.subject.code},EE1\n'
            f'unknown@example.com,{self.enrollment.subject.code},ME1\n'
        ).encode()
        file = SimpleUploadedFile('marks.csv', content, content_type='text/csv')

        response = self.client.post(
            '/api/v1/school-admin/marks/import/',
            {'period_id': self.period.id, 'preview': 'false', 'file': file},
            format='multipart',
        )

        assert response.status_code == 400
        assert response.data['message']['error_count'] == 1
        assert CBCGrade.objects.count() == 0
