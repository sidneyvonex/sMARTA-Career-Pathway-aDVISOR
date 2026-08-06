from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from accounts.response import _error, _success

from .models import CapturedEmail
from .serializers import CapturedEmailDetailSerializer, CapturedEmailListSerializer


class _DevOnlyView(APIView):
    """Base view for the dev mailbox. Unauthenticated by design (developers
    are often logged out), and hidden (404) whenever DEBUG is off."""

    permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


class LetterListView(_DevOnlyView):
    def get(self, request):
        letters = CapturedEmail.objects.all()  # Meta.ordering = -created_at
        return _success(data=CapturedEmailListSerializer(letters, many=True).data)

    def delete(self, request):
        deleted, _ = CapturedEmail.objects.all().delete()
        return _success(data={'deleted': deleted}, message='Inbox cleared.')


class LetterDetailView(_DevOnlyView):
    def get(self, request, pk):
        try:
            letter = CapturedEmail.objects.get(pk=pk)
        except CapturedEmail.DoesNotExist:
            return _error('Letter not found.', status.HTTP_404_NOT_FOUND)
        return _success(data=CapturedEmailDetailSerializer(letter).data)
