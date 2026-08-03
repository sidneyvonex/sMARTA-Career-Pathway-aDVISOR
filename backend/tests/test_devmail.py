import pytest

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
