from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsParent, IsEmailVerified
from accounts.response import _success, _error


class ParentChildrenView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsParent]

    def get(self, request):
        return _success(data=[])
