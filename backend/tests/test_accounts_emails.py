import pytest


@pytest.mark.django_db
class TestEmailTasks:
    def test_send_verification_email(self, mailoutbox):
        from accounts.emails import send_verification_email
        send_verification_email.delay(user_id=1, email='student@test.com', first_name='Alice')
        assert len(mailoutbox) == 1
        msg = mailoutbox[0]
        assert msg.to == ['student@test.com']
        assert 'Verify your CBC Guidance account' in msg.subject
        assert '/verify-email?token=' in msg.body

    def test_send_password_reset_email(self, mailoutbox):
        from accounts.emails import send_password_reset_email
        send_password_reset_email.delay(user_id=2, email='user@test.com', first_name='Bob')
        assert len(mailoutbox) == 1
        msg = mailoutbox[0]
        assert msg.to == ['user@test.com']
        assert 'Reset your CBC Guidance password' in msg.subject
        assert '/reset-password?token=' in msg.body

    def test_send_staff_invite_email(self, mailoutbox):
        from accounts.emails import send_staff_invite_email
        send_staff_invite_email.delay(invitee_email='counselor@school.com', role='counselor')
        assert len(mailoutbox) == 1
        msg = mailoutbox[0]
        assert msg.to == ['counselor@school.com']
        assert 'Counselor' in msg.subject
        assert '/accept-invite?token=' in msg.body

    def test_send_parent_invite_email(self, mailoutbox):
        from accounts.emails import send_parent_invite_email
        send_parent_invite_email.delay(student_id=5, parent_email='parent@test.com', student_name='Jane Doe')
        assert len(mailoutbox) == 1
        msg = mailoutbox[0]
        assert msg.to == ['parent@test.com']
        assert 'Jane Doe' in msg.subject
        assert '/accept-invite?token=' in msg.body
