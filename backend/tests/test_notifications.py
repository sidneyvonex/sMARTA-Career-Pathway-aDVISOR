import pytest
from django.contrib.auth import get_user_model
from notifications.models import Notification
from notifications.utils import create_notification
from tests.factories import VerifiedUserFactory

User = get_user_model()


@pytest.mark.django_db
class TestCreateNotification:
    def test_creates_notification_record(self):
        user = VerifiedUserFactory()
        create_notification(user, 'counselor_note', 'Your counselor left a note.')
        assert Notification.objects.filter(user=user).count() == 1

    def test_fields_are_set_correctly(self):
        user = VerifiedUserFactory()
        create_notification(user, 'parent_linked', 'Your parent has been linked.')
        notif = Notification.objects.get(user=user)
        assert notif.type == 'parent_linked'
        assert notif.message == 'Your parent has been linked.'
        assert notif.read is False
        assert notif.created_at is not None

    def test_multiple_notifications_for_same_user(self):
        user = VerifiedUserFactory()
        create_notification(user, 'assessment_submitted', 'Msg 1')
        create_notification(user, 'counselor_note', 'Msg 2')
        assert Notification.objects.filter(user=user).count() == 2
