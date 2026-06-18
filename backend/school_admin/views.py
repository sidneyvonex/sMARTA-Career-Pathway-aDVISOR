from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
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


MAX_LOGO_SIZE = 5 * 1024 * 1024
MAX_LOGO_DIM = 1000
ALLOWED_FORMATS = {'JPEG', 'PNG'}
FORMAT_TO_EXT = {'JPEG': 'jpg', 'PNG': 'png'}


class SchoolLogoUploadView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        logo = request.FILES.get('logo')
        if not logo:
            return _error('No logo file provided.')
        if logo.size > MAX_LOGO_SIZE:
            return _error('Logo must be 5MB or less.')

        file_bytes = logo.read()
        try:
            img = Image.open(BytesIO(file_bytes))
            img.verify()
            img = Image.open(BytesIO(file_bytes))
            fmt = img.format
        except Exception:
            return _error('Invalid image file.')

        if fmt not in ALLOWED_FORMATS:
            return _error('Only JPEG and PNG images are allowed.')

        try:
            if img.width > MAX_LOGO_DIM or img.height > MAX_LOGO_DIM:
                img.thumbnail((MAX_LOGO_DIM, MAX_LOGO_DIM), Image.LANCZOS)
            output = BytesIO()
            if fmt == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output, format=fmt)
            output.seek(0)
        except Exception:
            return _error('Invalid image file.')

        ext = FORMAT_TO_EXT[fmt]
        filename = f'school-logos/school_{school.id}.{ext}'
        saved_path = default_storage.save(filename, ContentFile(output.read()))
        logo_url = default_storage.url(saved_path)

        school.logo_url = logo_url
        school.save(update_fields=['logo_url'])
        return _success(data={'logo_url': logo_url}, message='School logo updated.')

    def delete(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)
        school.logo_url = None
        school.save(update_fields=['logo_url'])
        return _success(message='Logo removed.')
