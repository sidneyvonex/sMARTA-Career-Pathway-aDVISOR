from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsEmailVerified
from accounts.response import _success, _error
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        notifications = (
            Notification.objects
            .filter(user=request.user)
            .order_by('-created_at')[:50]
        )
        return _success(data=NotificationSerializer(notifications, many=True).data)


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, read=False).count()
        return _success(data={'count': count})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return _error('Notification not found.', status.HTTP_404_NOT_FOUND)
        notif.read = True
        notif.save(update_fields=['read'])
        return _success(data=NotificationSerializer(notif).data)


class MarkAllReadView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return _success(message='All notifications marked as read.')
