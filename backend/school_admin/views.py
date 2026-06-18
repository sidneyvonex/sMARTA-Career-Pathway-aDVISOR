from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import IsSchoolAdmin, IsEmailVerified
from accounts.models import User


def _success(data=None, message='', status_code=status.HTTP_200_OK):
    return Response({'data': data, 'error': None, 'message': message}, status=status_code)


def _error(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({'data': None, 'error': True, 'message': message}, status=status_code)


SCHOOL_EDITABLE_FIELDS = {'name', 'phone', 'email'}


class SchoolProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def _get_school(self, user):
        if not user.school:
            return None
        return user.school

    def _serialize(self, school):
        student_count = school.studentprofile_set.filter(mode='school_linked').count()
        counselor_count = User.objects.filter(school=school, role='counselor').count()
        return {
            'id': school.id,
            'name': school.name,
            'county': school.county,
            'school_code': school.school_code,
            'logo_url': school.logo_url,
            'phone': school.phone,
            'email': school.email,
            'student_count': student_count,
            'counselor_count': counselor_count,
        }

    def get(self, request):
        school = self._get_school(request.user)
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        return _success(data=self._serialize(school))

    def patch(self, request):
        school = self._get_school(request.user)
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        updated = []
        for field in SCHOOL_EDITABLE_FIELDS:
            if field in request.data:
                setattr(school, field, request.data[field])
                updated.append(field)
        if updated:
            school.save(update_fields=updated)
        return _success(data=self._serialize(school), message='School profile updated.')
