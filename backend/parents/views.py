from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsParent, IsEmailVerified
from accounts.response import _success
from parents.models import ParentStudentLink
from parents.serializers import LinkedChildSerializer


class ParentChildrenView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsParent]

    def get(self, request):
        links = (
            ParentStudentLink.objects
            .filter(parent=request.user)
            .select_related('student__student_profile')
        )
        data = LinkedChildSerializer(links, many=True).data
        return _success(data=data)
