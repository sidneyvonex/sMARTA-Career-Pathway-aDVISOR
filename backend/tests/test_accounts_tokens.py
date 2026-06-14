import pytest
from unittest.mock import patch
from django.test import override_settings
from accounts.tokens import (
    make_email_verify_token, load_email_verify_token,
    make_password_reset_token, load_password_reset_token,
    make_invite_token, load_invite_token,
    make_parent_invite_token, load_parent_invite_token,
    TokenExpiredError, TokenInvalidError,
)


class TestEmailVerifyToken:
    @override_settings(SECRET_KEY='test-secret-key')
    def test_make_and_load(self):
        token = make_email_verify_token(user_id=42)
        payload = load_email_verify_token(token)
        assert payload['user_id'] == 42

    def test_expired_token_raises(self):
        from django.core import signing as django_signing
        with patch('accounts.tokens.signing.loads', side_effect=django_signing.SignatureExpired('expired')):
            with pytest.raises(TokenExpiredError):
                load_email_verify_token('any-token')

    def test_invalid_token_raises(self):
        with pytest.raises(TokenInvalidError):
            load_email_verify_token('not-a-valid-token')


class TestPasswordResetToken:
    @override_settings(SECRET_KEY='test-secret-key')
    def test_make_and_load(self):
        token = make_password_reset_token(user_id=7)
        payload = load_password_reset_token(token)
        assert payload['user_id'] == 7

    def test_invalid_token_raises(self):
        with pytest.raises(TokenInvalidError):
            load_password_reset_token('bad-token')


class TestInviteToken:
    @override_settings(SECRET_KEY='test-secret-key')
    def test_make_and_load(self):
        token = make_invite_token(email='counselor@test.com', role='counselor')
        payload = load_invite_token(token)
        assert payload['email'] == 'counselor@test.com'
        assert payload['role'] == 'counselor'

    def test_invalid_token_raises(self):
        with pytest.raises(TokenInvalidError):
            load_invite_token('bad-token')


class TestParentInviteToken:
    @override_settings(SECRET_KEY='test-secret-key')
    def test_make_and_load(self):
        token = make_parent_invite_token(student_id=5, email='parent@test.com')
        payload = load_parent_invite_token(token)
        assert payload['student_id'] == 5
        assert payload['email'] == 'parent@test.com'

    def test_invalid_token_raises(self):
        with pytest.raises(TokenInvalidError):
            load_parent_invite_token('bad-token')
