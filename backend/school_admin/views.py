from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import IsSchoolAdmin, IsEmailVerified
from accounts.models import User, StudentProfile
from counselors.models import CounselorAssignment
from riasec.models import RIASECAssessment


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


class SchoolCounselorsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        counselors = (
            User.objects.filter(school=school, role='counselor')
            .annotate(
                student_count=Count(
                    'student_assignments',
                    filter=Q(student_assignments__is_active=True),
                )
            )
            .order_by('first_name', 'last_name')
        )

        data = [
            {
                'id': c.id,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'email': c.email,
                'student_count': c.student_count,
                'joined_at': c.created_at.isoformat(),
            }
            for c in counselors
        ]
        return _success(data=data)


class SchoolCounselorAddView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        email = request.data.get('email', '').lower().strip()
        if not email:
            return _error('Email is required.')

        try:
            counselor = User.objects.get(email=email, role='counselor')
        except User.DoesNotExist:
            return _error('No counselor found with that email.', status.HTTP_404_NOT_FOUND)

        if counselor.school is not None:
            return _error('This counselor is already assigned to a school.')
        counselor.school = school
        counselor.save(update_fields=['school'])
        return _success(
            data={'id': counselor.id, 'email': counselor.email},
            message=f'{counselor.first_name} {counselor.last_name} added to {school.name}.',
        )


class SchoolCounselorRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request, counselor_id):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        try:
            counselor = User.objects.get(pk=counselor_id, role='counselor', school=school)
        except User.DoesNotExist:
            return _error('Counselor not found at your school.', status.HTTP_404_NOT_FOUND)

        CounselorAssignment.objects.filter(
            counselor=counselor, school=school, is_active=True,
        ).update(is_active=False)

        counselor.school = None
        counselor.save(update_fields=['school'])
        return _success(message=f'{counselor.first_name} {counselor.last_name} removed from {school.name}.')


class SchoolStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        has_assessment = RIASECAssessment.objects.filter(student_profile=OuterRef('pk'))

        profiles = (
            StudentProfile.objects.filter(school=school, mode='school_linked')
            .select_related('user')
            .annotate(has_assessment=Exists(has_assessment))
            .prefetch_related(
                Prefetch(
                    'counselor_assignments',
                    queryset=CounselorAssignment.objects.filter(is_active=True).select_related('counselor'),
                ),
            )
            .order_by('user__first_name', 'user__last_name')
        )

        data = []
        for p in profiles:
            active_assignment = None
            for a in p.counselor_assignments.all():
                if a.is_active:
                    active_assignment = a
                    break

            data.append({
                'id': p.user.id,
                'first_name': p.user.first_name,
                'last_name': p.user.last_name,
                'email': p.user.email,
                'grade': p.grade,
                'photo_url': p.photo_url,
                'quiz_status': 'done' if p.has_assessment else 'pending',
                'counselor_id': active_assignment.counselor_id if active_assignment else None,
                'counselor_name': (
                    f'{active_assignment.counselor.first_name} {active_assignment.counselor.last_name}'
                    if active_assignment else None
                ),
            })
        return _success(data=data)


class SchoolStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        has_assessment = RIASECAssessment.objects.filter(student_profile=OuterRef('pk'))

        profiles = (
            StudentProfile.objects.filter(school=school, mode='school_linked')
            .annotate(has_assessment=Exists(has_assessment))
        )
        total_students = profiles.count()
        assessed = profiles.filter(has_assessment=True).count()
        assigned_ids = set(
            CounselorAssignment.objects.filter(school=school, is_active=True)
            .values_list('student_profile_id', flat=True)
        )
        unassigned = profiles.exclude(pk__in=assigned_ids).count()
        total_counselors = User.objects.filter(school=school, role='counselor').count()

        return _success(data={
            'total_students': total_students,
            'total_counselors': total_counselors,
            'assessed': assessed,
            'unassigned': unassigned,
        })


class SchoolAssignmentView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        student_id = request.data.get('student_id')
        counselor_id = request.data.get('counselor_id')

        try:
            profile = StudentProfile.objects.get(
                user_id=student_id, school=school, mode='school_linked',
            )
        except StudentProfile.DoesNotExist:
            return _error('Student not found at your school.', status.HTTP_404_NOT_FOUND)

        try:
            counselor = User.objects.get(pk=counselor_id, role='counselor', school=school)
        except User.DoesNotExist:
            return _error('Counselor not found at your school.', status.HTTP_404_NOT_FOUND)

        CounselorAssignment.objects.filter(
            student_profile=profile, is_active=True,
        ).update(is_active=False)

        assignment = CounselorAssignment.objects.create(
            counselor=counselor,
            student_profile=profile,
            school=school,
        )

        return _success(
            data={'id': assignment.id, 'student_id': student_id, 'counselor_id': counselor_id},
            message=f'{profile.user.first_name} assigned to {counselor.first_name} {counselor.last_name}.',
            status_code=status.HTTP_201_CREATED,
        )


class SchoolAssignmentRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def post(self, request, assignment_id):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', status.HTTP_404_NOT_FOUND)

        try:
            assignment = CounselorAssignment.objects.get(
                pk=assignment_id, school=school, is_active=True,
            )
        except CounselorAssignment.DoesNotExist:
            return _error('Assignment not found.', status.HTTP_404_NOT_FOUND)

        assignment.is_active = False
        assignment.save(update_fields=['is_active'])
        return _success(message='Assignment removed.')
