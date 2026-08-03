import pytest
from django.core import mail
from django.test import override_settings

from devmail.models import CapturedEmail
from tests.factories import CapturedEmailFactory

pytestmark = pytest.mark.django_db


def test_captured_email_orders_newest_first():
    older = CapturedEmailFactory(subject='Older')
    newer = CapturedEmailFactory(subject='Newer')
    # created_at is auto_now_add; force a deterministic order.
    CapturedEmail.objects.filter(pk=older.pk).update(
        created_at='2026-08-01T09:00:00Z'
    )
    CapturedEmail.objects.filter(pk=newer.pk).update(
        created_at='2026-08-02T09:00:00Z'
    )

    subjects = list(CapturedEmail.objects.values_list('subject', flat=True))

    assert subjects == ['Newer', 'Older']


@override_settings(EMAIL_BACKEND='devmail.backend.DevMailBackend')
def test_dev_mail_backend_persists_sent_email():
    sent = mail.send_mail(
        subject='Verify your CBC Guidance account',
        message='Click http://localhost:5173/verify-email?token=abc',
        from_email='noreply@cbcguidance.co.ke',
        recipient_list=['new.learner@test.com'],
    )

    assert sent == 1
    captured = CapturedEmail.objects.get()
    assert captured.to_email == 'new.learner@test.com'
    assert captured.from_email == 'noreply@cbcguidance.co.ke'
    assert captured.subject == 'Verify your CBC Guidance account'
    assert 'verify-email?token=abc' in captured.body


@override_settings(EMAIL_BACKEND='devmail.backend.DevMailBackend')
def test_dev_mail_backend_joins_multiple_recipients():
    mail.send_mail(
        subject='Invite',
        message='Body',
        from_email='noreply@cbcguidance.co.ke',
        recipient_list=['a@test.com', 'b@test.com'],
    )

    captured = CapturedEmail.objects.get()
    assert captured.to_email == 'a@test.com, b@test.com'
