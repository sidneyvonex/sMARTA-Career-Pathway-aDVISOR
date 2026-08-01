import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

import accounts.models as account_models
from accounts.serializers import StudentRegistrationSerializer
from notifications.models import Notification
from system_admin.models import AuditLog
from tests.factories import (
    CBCGradeFactory,
    CounselorAssignmentFactory,
    CounselorFactory,
    SchoolAdminFactory,
    SchoolFactory,
    StudentProfileFactory,
    StudentSchoolMembershipFactory,
    StudentSubjectFactory,
    UserFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db


def test_student_school_membership_model_exists():
    """Catches membership history being collapsed back into StudentProfile."""
    assert hasattr(account_models, 'StudentSchoolMembership')


@pytest.mark.parametrize(
    ('status', 'active_key', 'pending_key'),
    [
        ('active', 'profile', None),
        ('pending', None, 'profile'),
        ('ended', None, None),
        ('rejected', None, None),
    ],
)
def test_membership_derives_nullable_identity_keys(
    status,
    active_key,
    pending_key,
):
    """Catches lifecycle rows bypassing the MySQL-safe identity constraints."""
    profile = StudentProfileFactory()
    membership = StudentSchoolMembershipFactory(
        student_profile=profile,
        status=status,
    )

    assert membership.active_identity_key == (
        profile.pk if active_key == 'profile' else None
    )
    assert membership.pending_identity_key == (
        profile.pk if pending_key == 'profile' else None
    )


@pytest.mark.parametrize('status', ['active', 'pending'])
def test_only_one_current_membership_state_per_learner(status):
    """Catches concurrent active or pending memberships for one learner."""
    profile = StudentProfileFactory()
    StudentSchoolMembershipFactory(
        student_profile=profile,
        school=SchoolFactory(),
        status=status,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        StudentSchoolMembershipFactory(
            student_profile=profile,
            school=SchoolFactory(),
            status=status,
        )


def test_historical_memberships_remain_repeatable():
    """Catches uniqueness enforcement deleting or blocking transfer history."""
    profile = StudentProfileFactory()

    ended = StudentSchoolMembershipFactory.create_batch(
        2,
        student_profile=profile,
        status='ended',
    )
    rejected = StudentSchoolMembershipFactory.create_batch(
        2,
        student_profile=profile,
        status='rejected',
    )

    assert len(ended) == 2
    assert len(rejected) == 2


class TestLearnerMembershipRequests:
    url = '/api/v1/students/school-memberships/'

    def setup_method(self):
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.profile.user)

    def test_active_learner_requests_transfer_without_losing_current_school(self):
        """Catches a pending transfer prematurely removing current school access."""
        current_school = SchoolFactory()
        target_school = SchoolFactory(school_code='TARGET-001')
        self.profile.mode = 'school_linked'
        self.profile.school = current_school
        self.profile.school_membership_status = 'active'
        self.profile.save(
            update_fields=['mode', 'school', 'school_membership_status']
        )
        StudentSchoolMembershipFactory(
            student_profile=self.profile,
            school=current_school,
            status='active',
        )

        response = self.client.post(
            self.url,
            {'school_code': target_school.school_code},
            format='json',
        )

        assert response.status_code == 201
        self.profile.refresh_from_db()
        assert self.profile.school == current_school
        assert self.profile.school_membership_status == 'active'
        pending = self.profile.school_memberships.get(status='pending')
        assert pending.school == target_school
        assert response.data['data']['id'] == pending.id
        assert response.data['data']['status'] == 'pending'

        admin_client = APIClient()
        admin_client.force_authenticate(SchoolAdminFactory(school=target_school))
        requests = admin_client.get(
            '/api/v1/school-admin/membership-requests/'
        )
        stats = admin_client.get('/api/v1/school-admin/stats/')
        assert requests.status_code == 200
        assert requests.data['data'][0]['student_id'] == self.profile.user_id
        assert stats.data['data']['pending_memberships'] == 1

    def test_learner_without_active_school_exposes_pending_compatibility_state(self):
        """Catches first-time link requests disappearing from legacy consumers."""
        target_school = SchoolFactory(school_code='TARGET-002')

        response = self.client.post(
            self.url,
            {'school_code': target_school.school_code},
            format='json',
        )

        assert response.status_code == 201
        self.profile.refresh_from_db()
        assert self.profile.school == target_school
        assert self.profile.mode == 'school_linked'
        assert self.profile.school_membership_status == 'pending'

    def test_legacy_active_profile_without_history_stays_active_during_request(self):
        """Catches rollout-era learners losing current access before approval."""
        current_school = SchoolFactory()
        target_school = SchoolFactory()
        self.profile.mode = 'school_linked'
        self.profile.school = current_school
        self.profile.school_membership_status = 'active'
        self.profile.save(
            update_fields=['mode', 'school', 'school_membership_status']
        )

        response = self.client.post(
            self.url,
            {'school_code': target_school.school_code},
            format='json',
        )

        assert response.status_code == 201
        self.profile.refresh_from_db()
        assert self.profile.school == current_school
        assert self.profile.school_membership_status == 'active'

    @pytest.mark.parametrize(
        ('school_setup', 'payload', 'expected_status'),
        [
            ('missing', {'school_code': 'NO-SUCH-SCHOOL'}, 400),
            ('inactive', {}, 400),
        ],
    )
    def test_rejects_unavailable_target_schools(
        self,
        school_setup,
        payload,
        expected_status,
    ):
        """Catches transfer requests targeting unavailable school identities."""
        if school_setup == 'inactive':
            school = SchoolFactory(is_active=False)
            payload = {'school_code': school.school_code}

        response = self.client.post(self.url, payload, format='json')

        assert response.status_code == expected_status
        assert not self.profile.school_memberships.exists()

    def test_rejects_current_school_and_second_pending_request(self):
        """Catches duplicate or no-op transfer requests."""
        current_school = SchoolFactory()
        target_school = SchoolFactory()
        another_school = SchoolFactory()
        self.profile.mode = 'school_linked'
        self.profile.school = current_school
        self.profile.school_membership_status = 'active'
        self.profile.save(
            update_fields=['mode', 'school', 'school_membership_status']
        )
        StudentSchoolMembershipFactory(
            student_profile=self.profile,
            school=current_school,
            status='active',
        )

        current = self.client.post(
            self.url,
            {'school_code': current_school.school_code},
            format='json',
        )
        first = self.client.post(
            self.url,
            {'school_code': target_school.school_code},
            format='json',
        )
        second = self.client.post(
            self.url,
            {'school_code': another_school.school_code},
            format='json',
        )

        assert current.status_code == 400
        assert first.status_code == 201
        assert second.status_code == 409
        assert self.profile.school_memberships.filter(status='pending').count() == 1

    def test_lists_only_the_authenticated_learners_history(self):
        """Catches cross-learner membership history disclosure."""
        first = StudentSchoolMembershipFactory(
            student_profile=self.profile,
            status='ended',
        )
        second = StudentSchoolMembershipFactory(
            student_profile=self.profile,
            status='pending',
        )
        StudentSchoolMembershipFactory(status='active')

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert {row['id'] for row in response.data['data']} == {
            first.id,
            second.id,
        }

    def test_non_learner_cannot_request_membership(self):
        """Catches staff creating learner transfers through the learner route."""
        client = APIClient()
        client.force_authenticate(
            UserFactory(role='counselor', is_email_verified=True)
        )

        response = client.post(
            self.url,
            {'school_code': SchoolFactory().school_code},
            format='json',
        )

        assert response.status_code == 403


class TestSchoolMembershipTransferDecisions:
    def setup_method(self):
        self.old_school = SchoolFactory(name='Old School')
        self.target_school = SchoolFactory(name='Target School')
        self.profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            mode='school_linked',
            school=self.old_school,
            school_membership_status='active',
        )
        self.active = StudentSchoolMembershipFactory(
            student_profile=self.profile,
            school=self.old_school,
            status='active',
        )
        self.pending = StudentSchoolMembershipFactory(
            student_profile=self.profile,
            school=self.target_school,
            status='pending',
        )
        self.admin = SchoolAdminFactory(school=self.target_school)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.url = (
            '/api/v1/school-admin/membership-requests/'
            f'{self.profile.user_id}/decision/'
        )

    def test_approval_moves_membership_and_preserves_evidence(self):
        """Catches approval deleting evidence or leaving old access active."""
        enrollment = StudentSubjectFactory(student_profile=self.profile)
        grade = CBCGradeFactory(student_subject=enrollment)
        old_assignment = CounselorAssignmentFactory(
            student_profile=self.profile,
            counselor=CounselorFactory(school=self.old_school),
            school=self.old_school,
        )

        response = self.client.put(
            self.url,
            {'decision': 'approve'},
            format='json',
        )

        assert response.status_code == 200
        self.active.refresh_from_db()
        self.pending.refresh_from_db()
        self.profile.refresh_from_db()
        old_assignment.refresh_from_db()
        assert self.active.status == 'ended'
        assert self.active.ended_at is not None
        assert self.pending.status == 'active'
        assert self.pending.started_at is not None
        assert self.pending.decided_by == self.admin
        assert self.profile.school == self.target_school
        assert self.profile.school_membership_status == 'active'
        assert old_assignment.is_active is False
        assert enrollment.grades.filter(pk=grade.pk).exists()

        audit = AuditLog.objects.get(
            action='school_membership_approved',
            target_id=self.profile.user_id,
        )
        assert audit.details['membership_id'] == self.pending.id
        assert audit.details['previous_school_id'] == self.old_school.id
        notification = Notification.objects.get(
            user=self.profile.user,
            type='school_membership_decided',
        )
        assert self.target_school.name in notification.message

    def test_rejection_keeps_current_membership_and_assignment(self):
        """Catches rejected transfers disturbing the learner's current school."""
        assignment = CounselorAssignmentFactory(
            student_profile=self.profile,
            counselor=CounselorFactory(school=self.old_school),
            school=self.old_school,
        )

        response = self.client.put(
            self.url,
            {'decision': 'reject'},
            format='json',
        )

        assert response.status_code == 200
        self.active.refresh_from_db()
        self.pending.refresh_from_db()
        self.profile.refresh_from_db()
        assignment.refresh_from_db()
        assert self.active.status == 'active'
        assert self.pending.status == 'rejected'
        assert self.profile.school == self.old_school
        assert self.profile.school_membership_status == 'active'
        assert assignment.is_active is True

    def test_other_school_cannot_decide_target_request(self):
        """Catches school administrators deciding another school's transfer."""
        client = APIClient()
        client.force_authenticate(SchoolAdminFactory(school=SchoolFactory()))

        response = client.put(
            self.url,
            {'decision': 'approve'},
            format='json',
        )

        assert response.status_code == 404
        self.pending.refresh_from_db()
        assert self.pending.status == 'pending'

    def test_approval_rolls_back_every_state_when_notification_fails(
        self,
        monkeypatch,
    ):
        """Catches partial transfers committed before downstream side effects."""
        assignment = CounselorAssignmentFactory(
            student_profile=self.profile,
            counselor=CounselorFactory(school=self.old_school),
            school=self.old_school,
        )

        def fail_notification(**kwargs):
            raise RuntimeError('notification store unavailable')

        monkeypatch.setattr(Notification.objects, 'create', fail_notification)

        with pytest.raises(RuntimeError, match='notification store unavailable'):
            self.client.put(
                self.url,
                {'decision': 'approve'},
                format='json',
            )

        self.active.refresh_from_db()
        self.pending.refresh_from_db()
        self.profile.refresh_from_db()
        assignment.refresh_from_db()
        assert self.active.status == 'active'
        assert self.pending.status == 'pending'
        assert self.profile.school == self.old_school
        assert assignment.is_active is True
        assert not AuditLog.objects.filter(
            action='school_membership_approved',
            target_id=self.profile.user_id,
        ).exists()


def test_school_linked_registration_creates_pending_membership_history():
    """Catches new registrations existing only in compatibility fields."""
    school = SchoolFactory(county='kiambu')
    serializer = StudentRegistrationSerializer(
        data={
            'email': 'membership-registration@example.com',
            'password': 'TestPass123!',
            'first_name': 'Membership',
            'last_name': 'Learner',
            'county': 'kiambu',
            'grade': 10,
            'school_code': school.school_code,
            'role': 'student',
        }
    )

    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    membership = user.student_profile.school_memberships.get()
    assert membership.school == school
    assert membership.status == 'pending'


class TestMembershipVerificationSafety:
    def test_learner_cannot_edit_or_delete_verified_evidence(self):
        """Catches verified evidence mutation through learner grade routes."""
        school = SchoolFactory()
        admin = SchoolAdminFactory(school=school)
        profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
        )
        enrollment = StudentSubjectFactory(student_profile=profile)
        grade = CBCGradeFactory(
            student_subject=enrollment,
            verified_by=admin,
            verified_school=school,
            verified_at='2026-07-30T10:00:00Z',
        )
        url = (
            f'/api/v1/students/my-subjects/{enrollment.id}/grades/{grade.id}/'
        )
        client = APIClient()
        client.force_authenticate(profile.user)

        update = client.put(
            url,
            {'term': 1, 'year': 2026, 'level': 'EE1'},
            format='json',
        )
        delete = client.delete(url)

        assert update.status_code == 403
        assert delete.status_code == 403
        grade.refresh_from_db()
        assert grade.level == 'ME1'

    def test_verifying_school_cannot_remove_verification_after_membership_ends(self):
        """Catches stale compatibility fields granting former-school access."""
        school = SchoolFactory()
        admin = SchoolAdminFactory(school=school)
        profile = StudentProfileFactory(
            mode='school_linked',
            school=school,
            school_membership_status='active',
        )
        StudentSchoolMembershipFactory(
            student_profile=profile,
            school=school,
            status='ended',
        )
        enrollment = StudentSubjectFactory(student_profile=profile)
        grade = CBCGradeFactory(
            student_subject=enrollment,
            verified_by=admin,
            verified_school=school,
            verified_at='2026-07-30T10:00:00Z',
        )
        client = APIClient()
        client.force_authenticate(admin)

        response = client.put(
            '/api/v1/school-admin/students/'
            f'{profile.user_id}/grades/{grade.id}/verification/',
            {'verified': False},
            format='json',
        )

        assert response.status_code == 404
        grade.refresh_from_db()
        assert grade.verified_at is not None
