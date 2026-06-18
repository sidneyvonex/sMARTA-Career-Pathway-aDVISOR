from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from accounts.permissions import IsParent, IsEmailVerified
from accounts.response import _success, _error
from accounts.models import StudentProfile
from parents.models import ParentStudentLink
from parents.serializers import LinkedChildSerializer, ChildDetailSerializer


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


class ParentChildDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsParent]

    def get(self, request, student_id):
        if not ParentStudentLink.objects.filter(
            parent=request.user, student_id=student_id,
        ).exists():
            return _error('Child not found.', status.HTTP_404_NOT_FOUND)

        try:
            profile = StudentProfile.objects.select_related('user').get(user_id=student_id)
        except StudentProfile.DoesNotExist:
            return _error('Student profile not found.', status.HTTP_404_NOT_FOUND)

        data = ChildDetailSerializer(profile).data
        return _success(data=data)
