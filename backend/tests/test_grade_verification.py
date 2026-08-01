import pytest
from rest_framework.test import APIClient

from students.models import CBCGrade
from system_admin.models import AuditLog
from tests.factories import (
    CBCGradeFactory,
    CounselorFactory,
    SchoolAdminFactory,
    SchoolFactory,
    StudentProfileFactory,
    StudentSubjectFactory,
    UserFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db


def verification_url(profile, grade):
    return (
        f'/api/v1/school-admin/students/{profile.user_id}/'
        f'grades/{grade.id}/verification/'
    )


class TestGradeProvenanceModel:
    def test_learner_is_default_source(self):
        grade = CBCGradeFactory()

        assert grade.source == 'learner'
        assert grade.verified_by is None
        assert grade.verified_at is None

    def test_school_source_is_supported(self):
        grade = CBCGradeFactory(source='school')

        assert grade.source == 'school'


class TestLearnerGradeProvenanceProtection:
    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student')
        )
        self.enrollment = StudentSubjectFactory(student_profile=self.profile)
        self.client = APIClient()
        self.client.force_authenticate(self.profile.user)

    def test_learner_cannot_forge_source_or_verification_on_create(self):
        verifier = SchoolAdminFactory()

        response = self.client.post(
            f'/api/v1/students/my-subjects/{self.enrollment.id}/grades/',
            {
                'term': 1,
                'year': 2026,
                'level': 'ME1',
                'source': 'school',
                'verified_by': verifier.id,
                'verified_at': '2026-07-30T10:00:00Z',
            },
            format='json',
        )

        assert response.status_code == 201
        grade = CBCGrade.objects.get(pk=response.data['data']['id'])
        assert grade.source == 'learner'
        assert grade.verified_by is None
        assert grade.verified_at is None
        assert response.data['data']['source'] == 'learner'

    def test_learner_update_does_not_clear_existing_verification(self):
        verifier = SchoolAdminFactory()
        grade = CBCGradeFactory(
            student_subject=self.enrollment,
            verified_by=verifier,
            verified_at='2026-07-30T10:00:00Z',
        )

        response = self.client.put(
            f'/api/v1/students/my-subjects/{self.enrollment.id}/grades/{grade.id}/',
            {
                'term': grade.term,
                'year': grade.year,
                'level': 'EE1',
                'verified_by': None,
                'verified_at': None,
            },
            format='json',
        )

        assert response.status_code == 200
        grade.refresh_from_db()
        assert grade.verified_by == verifier
        assert grade.verified_at is not None


class TestSchoolGradeVerification:
    def setup_method(self):
        self.school = SchoolFactory(county='kiambu')
        self.admin = SchoolAdminFactory(school=self.school)
        self.profile = StudentProfileFactory(
            school=self.school,
            mode='school_linked',
            school_membership_status='active',
        )
        self.grade = CBCGradeFactory(
            student_subject=StudentSubjectFactory(student_profile=self.profile)
        )
        self.url = verification_url(self.profile, self.grade)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_school_admin_can_verify_grade(self):
        response = self.client.put(
            self.url,
            {'verified': True},
            format='json',
        )

        assert response.status_code == 200
        self.grade.refresh_from_db()
        assert self.grade.verified_by == self.admin
        assert self.grade.verified_at is not None
        assert response.data['data']['verified_by'] == self.admin.id

    def test_school_admin_can_remove_verification(self):
        self.grade.verified_by = self.admin
        self.grade.verified_at = '2026-07-30T10:00:00Z'
        self.grade.verified_school = self.school
        self.grade.save(
            update_fields=['verified_by', 'verified_at', 'verified_school']
        )

        response = self.client.put(
            self.url,
            {'verified': False},
            format='json',
        )

        assert response.status_code == 200
        self.grade.refresh_from_db()
        assert self.grade.verified_by is None
        assert self.grade.verified_at is None

    @pytest.mark.parametrize('should_verify', [True, False])
    def test_current_school_cannot_mutate_another_schools_provenance(
        self,
        should_verify,
    ):
        """Catches transfer membership overriding the historical verifying school."""
        original_school = SchoolFactory()
        original_admin = SchoolAdminFactory(school=original_school)
        grade = CBCGradeFactory(
            student_subject=self.grade.student_subject,
            term=2,
            verified_by=original_admin,
            verified_at='2026-07-30T10:00:00Z',
            verified_school=original_school,
        )

        response = self.client.put(
            verification_url(self.profile, grade),
            {'verified': should_verify},
            format='json',
        )

        assert response.status_code == 403
        assert response.data['data'] is None
        assert response.data['error'] is True
        grade.refresh_from_db()
        assert grade.verified_by == original_admin
        assert grade.verified_school == original_school

    @pytest.mark.parametrize('should_verify', [True, False])
    def test_school_cannot_mutate_legacy_verification_without_school_provenance(
        self,
        should_verify,
    ):
        """Catches guessing ownership for legacy verified evidence."""
        CBCGrade.objects.filter(pk=self.grade.pk).update(
            verified_by=self.admin,
            verified_at='2026-07-30T10:00:00Z',
            verified_school=None,
        )

        response = self.client.put(
            self.url,
            {'verified': should_verify},
            format='json',
        )

        assert response.status_code == 403
        assert response.data['data'] is None
        assert response.data['error'] is True
        self.grade.refresh_from_db()
        assert self.grade.verified_by == self.admin
        assert self.grade.verified_school is None

    def test_verification_and_removal_are_audited(self):
        self.client.put(self.url, {'verified': True}, format='json')
        self.client.put(self.url, {'verified': False}, format='json')

        logs = AuditLog.objects.filter(
            target_type='grade',
            target_id=self.grade.id,
        ).order_by('created_at')
        assert [log.action for log in logs] == [
            'grade_verified',
            'grade_verification_removed',
        ]
        assert all(log.actor == self.admin for log in logs)
        assert all(log.details['student_id'] == self.profile.user_id for log in logs)

    def test_repeating_same_state_does_not_create_duplicate_audit(self):
        self.client.put(self.url, {'verified': True}, format='json')
        self.client.put(self.url, {'verified': True}, format='json')

        assert AuditLog.objects.filter(
            action='grade_verified',
            target_type='grade',
            target_id=self.grade.id,
        ).count() == 1

    def test_grade_at_another_school_is_not_accessible(self):
        other_profile = StudentProfileFactory(
            school=SchoolFactory(),
            mode='school_linked',
            school_membership_status='active',
        )
        other_grade = CBCGradeFactory(
            student_subject=StudentSubjectFactory(student_profile=other_profile)
        )

        response = self.client.put(
            verification_url(other_profile, other_grade),
            {'verified': True},
            format='json',
        )

        assert response.status_code == 404

    def test_pending_learner_grade_is_not_verifiable(self):
        self.profile.school_membership_status = 'pending'
        self.profile.save(update_fields=['school_membership_status'])

        response = self.client.put(
            self.url,
            {'verified': True},
            format='json',
        )

        assert response.status_code == 404

    def test_inactive_school_cannot_verify(self):
        self.school.is_active = False
        self.school.save(update_fields=['is_active'])

        response = self.client.put(
            self.url,
            {'verified': True},
            format='json',
        )

        assert response.status_code == 403

    @pytest.mark.parametrize('payload', [{}, {'verified': 'yes'}, {'verified': 1}])
    def test_verified_must_be_a_boolean(self, payload):
        response = self.client.put(self.url, payload, format='json')

        assert response.status_code == 400
        self.grade.refresh_from_db()
        assert self.grade.verified_at is None

    def test_non_school_admin_is_rejected(self):
        client = APIClient()
        client.force_authenticate(CounselorFactory(school=self.school))

        assert client.put(
            self.url,
            {'verified': True},
            format='json',
        ).status_code == 403

    def test_unverified_school_admin_is_rejected(self):
        client = APIClient()
        client.force_authenticate(
            UserFactory(
                role='school_admin',
                school=self.school,
                is_email_verified=False,
            )
        )

        assert client.put(
            self.url,
            {'verified': True},
            format='json',
        ).status_code == 403
