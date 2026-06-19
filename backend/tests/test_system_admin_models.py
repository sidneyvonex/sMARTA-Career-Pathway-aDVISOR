import pytest
from tests.factories import AuditLogFactory, SystemAdminFactory, SchoolFactory
from system_admin.models import AuditLog
from system_admin.utils import log_action
from accounts.models import School

pytestmark = pytest.mark.django_db


class TestAuditLogModel:
    def test_create_audit_log(self):
        log = AuditLogFactory()
        assert log.action == 'school_created'
        assert log.target_type == 'school'
        assert log.details == {}
        assert log.created_at is not None

    def test_audit_log_with_details(self):
        log = AuditLogFactory(
            action='invite_sent',
            target_type='user',
            target_id=42,
            details={'email': 'test@example.com', 'role': 'counselor'},
        )
        assert log.details['email'] == 'test@example.com'
        assert log.details['role'] == 'counselor'

    def test_audit_log_actor_nullable(self):
        log = AuditLogFactory(actor=None)
        assert log.actor is None

    def test_ordering_newest_first(self):
        log1 = AuditLogFactory()
        log2 = AuditLogFactory()
        logs = list(AuditLog.objects.all())
        assert logs[0].id == log2.id
        assert logs[1].id == log1.id

    def test_str_representation(self):
        log = AuditLogFactory()
        s = str(log)
        assert 'school_created' in s


class TestLogActionUtility:
    def test_log_action_creates_entry(self):
        admin = SystemAdminFactory()
        log_action(
            actor=admin,
            action='school_created',
            target_type='school',
            target_id=1,
            details={'name': 'Test School'},
        )
        assert AuditLog.objects.count() == 1
        entry = AuditLog.objects.first()
        assert entry.actor == admin
        assert entry.action == 'school_created'
        assert entry.details['name'] == 'Test School'

    def test_log_action_extracts_ip_from_request(self):
        admin = SystemAdminFactory()

        class FakeRequest:
            META = {'REMOTE_ADDR': '192.168.1.1'}

        log_action(
            actor=admin,
            action='user_registered',
            target_type='user',
            target_id=1,
            request=FakeRequest(),
        )
        entry = AuditLog.objects.first()
        assert entry.ip_address == '192.168.1.1'

    def test_log_action_prefers_x_forwarded_for(self):
        admin = SystemAdminFactory()

        class FakeRequest:
            META = {
                'HTTP_X_FORWARDED_FOR': '10.0.0.1, 10.0.0.2',
                'REMOTE_ADDR': '192.168.1.1',
            }

        log_action(
            actor=admin,
            action='user_registered',
            target_type='user',
            target_id=1,
            request=FakeRequest(),
        )
        entry = AuditLog.objects.first()
        assert entry.ip_address == '10.0.0.1'

    def test_log_action_no_request(self):
        admin = SystemAdminFactory()
        log_action(
            actor=admin,
            action='email_verified',
            target_type='user',
            target_id=1,
        )
        entry = AuditLog.objects.first()
        assert entry.ip_address is None


class TestSchoolIsActive:
    def test_school_default_is_active(self):
        school = SchoolFactory()
        assert school.is_active is True

    def test_school_can_be_deactivated(self):
        school = SchoolFactory()
        school.is_active = False
        school.save(update_fields=['is_active'])
        school.refresh_from_db()
        assert school.is_active is False
