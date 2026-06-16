import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from notifications.models import Notification
from notifications.utils import create_notification
from tests.factories import VerifiedUserFactory, NotificationFactory

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


@pytest.mark.django_db
class TestNotificationListView:
    def setup_method(self):
        self.client = APIClient()
        self.user = VerifiedUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_returns_own_notifications_only(self):
        NotificationFactory(user=self.user, message='Mine')
        other = VerifiedUserFactory()
        NotificationFactory(user=other, message='Not mine')
        res = self.client.get('/api/v1/notifications/')
        assert res.status_code == 200
        assert len(res.data['data']) == 1
        assert res.data['data'][0]['message'] == 'Mine'

    def test_ordered_newest_first(self):
        n1 = NotificationFactory(user=self.user, message='First')
        n2 = NotificationFactory(user=self.user, message='Second')
        res = self.client.get('/api/v1/notifications/')
        ids = [n['id'] for n in res.data['data']]
        assert ids.index(n2.id) < ids.index(n1.id)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        res = self.client.get('/api/v1/notifications/')
        assert res.status_code == 401

    def test_max_50_returned(self):
        for _ in range(55):
            NotificationFactory(user=self.user)
        res = self.client.get('/api/v1/notifications/')
        assert len(res.data['data']) == 50


@pytest.mark.django_db
class TestUnreadCountView:
    def setup_method(self):
        self.client = APIClient()
        self.user = VerifiedUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_returns_correct_unread_count(self):
        NotificationFactory(user=self.user, read=False)
        NotificationFactory(user=self.user, read=False)
        NotificationFactory(user=self.user, read=True)
        res = self.client.get('/api/v1/notifications/unread-count/')
        assert res.status_code == 200
        assert res.data['data']['count'] == 2

    def test_returns_zero_when_all_read(self):
        NotificationFactory(user=self.user, read=True)
        res = self.client.get('/api/v1/notifications/unread-count/')
        assert res.data['data']['count'] == 0

    def test_counts_only_own_notifications(self):
        other = VerifiedUserFactory()
        NotificationFactory(user=other, read=False)
        res = self.client.get('/api/v1/notifications/unread-count/')
        assert res.data['data']['count'] == 0


@pytest.mark.django_db
class TestNotificationReadView:
    def setup_method(self):
        self.client = APIClient()
        self.user = VerifiedUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_marks_notification_as_read(self):
        notif = NotificationFactory(user=self.user, read=False)
        res = self.client.patch(f'/api/v1/notifications/{notif.id}/read/')
        assert res.status_code == 200
        notif.refresh_from_db()
        assert notif.read is True

    def test_cannot_read_another_users_notification(self):
        other = VerifiedUserFactory()
        notif = NotificationFactory(user=other, read=False)
        res = self.client.patch(f'/api/v1/notifications/{notif.id}/read/')
        assert res.status_code == 404

    def test_returns_updated_notification(self):
        notif = NotificationFactory(user=self.user, read=False)
        res = self.client.patch(f'/api/v1/notifications/{notif.id}/read/')
        assert res.data['data']['read'] is True
        assert res.data['data']['id'] == notif.id

    def test_already_read_notification_returns_200(self):
        notif = NotificationFactory(user=self.user, read=True)
        res = self.client.patch(f'/api/v1/notifications/{notif.id}/read/')
        assert res.status_code == 200
        notif.refresh_from_db()
        assert notif.read is True


@pytest.mark.django_db
class TestMarkAllReadView:
    def setup_method(self):
        self.client = APIClient()
        self.user = VerifiedUserFactory()
        self.client.force_authenticate(user=self.user)

    def test_marks_all_unread_as_read(self):
        NotificationFactory(user=self.user, read=False)
        NotificationFactory(user=self.user, read=False)
        NotificationFactory(user=self.user, read=True)
        res = self.client.post('/api/v1/notifications/mark-all-read/')
        assert res.status_code == 200
        assert Notification.objects.filter(user=self.user, read=False).count() == 0

    def test_does_not_affect_other_users(self):
        other = VerifiedUserFactory()
        NotificationFactory(user=other, read=False)
        self.client.post('/api/v1/notifications/mark-all-read/')
        assert Notification.objects.filter(user=other, read=False).count() == 1
