import pytest
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient

from accounts.emails import send_verification_email
from devmail.models import CapturedEmail
from tests.factories import CapturedEmailFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


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


def test_letter_list_returns_newest_first(api_client):
    older = CapturedEmailFactory(subject='Older')
    newer = CapturedEmailFactory(subject='Newer')
    CapturedEmail.objects.filter(pk=older.pk).update(created_at='2026-08-01T09:00:00Z')
    CapturedEmail.objects.filter(pk=newer.pk).update(created_at='2026-08-02T09:00:00Z')

    response = api_client.get('/api/v1/dev/letters/')

    assert response.status_code == 200
    body = response.json()
    assert body['error'] is None
    assert [row['subject'] for row in body['data']] == ['Newer', 'Older']
    assert set(body['data'][0].keys()) == {'id', 'to_email', 'subject', 'created_at'}


def test_letter_detail_returns_full_body(api_client):
    letter = CapturedEmailFactory(
        subject='Reset your CBC Guidance password',
        body='Reset link: http://localhost:5173/reset-password?token=xyz',
    )

    response = api_client.get(f'/api/v1/dev/letters/{letter.pk}/')

    assert response.status_code == 200
    data = response.json()['data']
    assert data['subject'] == 'Reset your CBC Guidance password'
    assert 'reset-password?token=xyz' in data['body']
    assert 'from_email' in data


def test_letter_detail_missing_returns_404(api_client):
    response = api_client.get('/api/v1/dev/letters/999999/')

    assert response.status_code == 404
    assert response.json()['error'] is True


def test_clear_inbox_deletes_all_letters(api_client):
    CapturedEmailFactory.create_batch(3)

    response = api_client.delete('/api/v1/dev/letters/')

    assert response.status_code == 200
    assert response.json()['data']['deleted'] == 3
    assert CapturedEmail.objects.count() == 0


@override_settings(DEBUG=False)
def test_endpoints_return_404_in_production_mode(api_client):
    letter = CapturedEmailFactory()

    assert api_client.get('/api/v1/dev/letters/').status_code == 404
    assert api_client.get(f'/api/v1/dev/letters/{letter.pk}/').status_code == 404
    assert api_client.delete('/api/v1/dev/letters/').status_code == 404


@override_settings(EMAIL_BACKEND='devmail.backend.DevMailBackend')
def test_verification_email_flows_into_the_mailbox():
    user = UserFactory(email='new.grad@test.com', first_name='Njeri')

    # Eager Celery in test settings runs this synchronously.
    send_verification_email(user.id, user.email, user.first_name)

    captured = CapturedEmail.objects.get()
    assert captured.to_email == 'new.grad@test.com'
    assert captured.subject == 'Verify your CBC Guidance account'
    assert '/verify-email?token=' in captured.body
