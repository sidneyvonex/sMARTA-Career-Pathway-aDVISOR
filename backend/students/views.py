from io import BytesIO
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from PIL import Image
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsStudent, IsEmailVerified
from accounts.models import StudentProfile
from accounts.response import _success, _error
from guidance.models import (
    FrameworkVersion,
    LearnerCombinationChoice,
    SchoolOffering,
)
from guidance.selectors import active_combination_queryset
from guidance.serializers import (
    LearnerCombinationChoiceCreateSerializer,
    LearnerCombinationChoiceSerializer,
)
from .models import Subject, StudentSubject, CBCGrade
from .serializers import (
    StudentProfileSerializer, SubjectSerializer,
    StudentSubjectSerializer, CBCGradeSerializer,
)
from .summaries import (
    academic_evidence_summary,
    assessment_summary,
    grade_summary,
    next_action_for,
    profile_completion_summary,
)

MAX_PHOTO_SIZE = 5 * 1024 * 1024
MAX_PHOTO_DIM = 2000
ALLOWED_FORMATS = {'JPEG', 'PNG'}
FORMAT_TO_MIME = {'JPEG': 'image/jpeg', 'PNG': 'image/png'}
FORMAT_TO_EXT = {'JPEG': 'jpg', 'PNG': 'png'}


def learner_choice_queryset(profile):
    active_offerings = (
        SchoolOffering.objects
        .filter(is_active=True, school__is_active=True)
        .select_related('school')
        .order_by('school__name')
    )
    return (
        LearnerCombinationChoice.objects
        .filter(student_profile=profile)
        .select_related(
            'combination__framework_version',
            'combination__track__pathway',
            'combination__subject_one',
            'combination__subject_two',
            'combination__subject_three',
        )
        .prefetch_related(
            Prefetch(
                'combination__school_offerings',
                queryset=active_offerings,
                to_attr='active_school_offerings',
            )
        )
    )


class EvidenceSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = (
            StudentProfile.objects
            .annotate(
                saved_combination_count=Count('combination_choices'),
                provisional_combination_count=Count(
                    'combination_choices',
                    filter=Q(
                        combination_choices__status=(
                            LearnerCombinationChoice.STATUS_PROVISIONAL
                        )
                    ),
                ),
            )
            .get(user=request.user)
        )
        profile_completion = profile_completion_summary(profile)
        academic_evidence = academic_evidence_summary(profile)
        assessment = assessment_summary(profile)
        saved_combination_count = profile.saved_combination_count
        has_provisional_choice = profile.provisional_combination_count > 0
        plan_status = 'not_started'
        return _success(
            data={
                'profile_completion': profile_completion,
                'academic_evidence': academic_evidence,
                'assessment': assessment,
                'saved_combination_count': saved_combination_count,
                'plan_status': plan_status,
                'next_action': next_action_for(
                    profile_completion,
                    academic_evidence,
                    assessment,
                    saved_combination_count,
                    has_provisional_choice=has_provisional_choice,
                    plan_status=plan_status,
                ),
            }
        )


class LearnerCombinationChoiceListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        choices = learner_choice_queryset(profile)
        return _success(
            data=LearnerCombinationChoiceSerializer(choices, many=True).data
        )

    def post(self, request):
        serializer = LearnerCombinationChoiceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)

        framework = FrameworkVersion.objects.current()
        if framework is None:
            return _error('No active guidance framework found.')
        combination = get_object_or_404(
            active_combination_queryset(framework),
            pk=serializer.validated_data['combination_id'],
        )

        with transaction.atomic():
            profile = StudentProfile.objects.select_for_update().get(
                user=request.user
            )
            choices = LearnerCombinationChoice.objects.filter(
                student_profile=profile
            )
            if choices.filter(combination=combination).exists():
                return _error('This combination is already saved.')
            if choices.count() >= 3:
                return _error('You can save a maximum of three combinations.')
            choice = LearnerCombinationChoice.objects.create(
                student_profile=profile,
                combination=combination,
                learner_reason=serializer.validated_data['learner_reason'],
            )

        return _success(
            data=LearnerCombinationChoiceSerializer(choice).data,
            message='Combination saved.',
            status_code=status.HTTP_201_CREATED,
        )


class LearnerCombinationChoiceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def delete(self, request, choice_id):
        profile = StudentProfile.objects.get(user=request.user)
        choice = get_object_or_404(
            LearnerCombinationChoice,
            pk=choice_id,
            student_profile=profile,
        )
        if choice.status == LearnerCombinationChoice.STATUS_PROVISIONAL:
            return _error(
                'Change the provisional choice before removing this combination.'
            )
        choice.delete()
        return _success(
            message='Saved combination removed.',
            status_code=status.HTTP_204_NO_CONTENT,
        )


class LearnerCombinationChoiceProvisionalView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def put(self, request, choice_id):
        with transaction.atomic():
            profile = StudentProfile.objects.select_for_update().get(
                user=request.user
            )
            choice = get_object_or_404(
                learner_choice_queryset(profile).select_for_update(),
                pk=choice_id,
            )
            (
                LearnerCombinationChoice.objects
                .filter(
                    student_profile=profile,
                    status=LearnerCombinationChoice.STATUS_PROVISIONAL,
                )
                .exclude(pk=choice.pk)
                .update(status=LearnerCombinationChoice.STATUS_SAVED)
            )
            if choice.status != LearnerCombinationChoice.STATUS_PROVISIONAL:
                choice.status = LearnerCombinationChoice.STATUS_PROVISIONAL
                choice.save(update_fields=['status', 'updated_at'])

        return _success(
            data=LearnerCombinationChoiceSerializer(choice).data,
            message='Provisional combination updated.',
        )


class GradeSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        return _success(data=grade_summary(profile))


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.select_related('user', 'school').get(user=request.user)
        return _success(data=StudentProfileSerializer(profile).data)

    def patch(self, request):
        profile = StudentProfile.objects.select_related('user').get(user=request.user)
        serializer = StudentProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return _error(serializer.errors)
        serializer.save()
        return _success(data=serializer.data, message='Profile updated.')


class PhotoUploadView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def post(self, request):
        photo = request.FILES.get('photo')
        if not photo:
            return _error('No photo file provided.')
        if photo.size > MAX_PHOTO_SIZE:
            return _error('Photo must be 5MB or less.')

        file_bytes = photo.read()

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
            if img.width > MAX_PHOTO_DIM or img.height > MAX_PHOTO_DIM:
                img.thumbnail((MAX_PHOTO_DIM, MAX_PHOTO_DIM), Image.LANCZOS)
            output = BytesIO()
            if fmt == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output, format=fmt)
            output.seek(0)
        except Exception:
            return _error('Invalid image file.')

        ext = FORMAT_TO_EXT[fmt]
        filename = f'profile-photos/user_{request.user.id}.{ext}'
        saved_path = default_storage.save(filename, ContentFile(output.read()))
        photo_url = default_storage.url(saved_path)

        profile = StudentProfile.objects.get(user=request.user)
        profile.photo_url = photo_url
        profile.save(update_fields=['photo_url'])
        return _success(data={'photo_url': photo_url}, message='Photo updated.')

    def delete(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        profile.photo_url = None
        profile.save(update_fields=['photo_url'])
        return _success(message='Photo removed.')


class SubjectListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        grade_param = request.query_params.get('grade')
        qs = Subject.objects.filter(is_active=True)
        if grade_param is not None:
            try:
                qs = qs.filter(grade=int(grade_param))
            except ValueError:
                return _error('Grade must be 9 or 10.')
        return _success(data=SubjectSerializer(qs, many=True).data)


class MySubjectListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        qs = StudentSubject.objects.filter(student_profile=profile).select_related('subject')
        return _success(data=StudentSubjectSerializer(qs, many=True).data)

    def post(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        serializer = StudentSubjectSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)
        subject = serializer.validated_data['subject']
        if subject.grade != profile.grade:
            return _error(
                f'Subject is for Grade {subject.grade}, but you are in Grade {profile.grade}.'
            )
        if StudentSubject.objects.filter(student_profile=profile, subject=subject).exists():
            return _error('You are already enrolled in this subject.')
        ss = StudentSubject.objects.create(student_profile=profile, subject=subject)
        return _success(
            data=StudentSubjectSerializer(ss).data,
            message='Subject added.',
            status_code=status.HTTP_201_CREATED,
        )


class MySubjectRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def post(self, request, pk):
        if not request.data.get('confirm'):
            return _error('Set confirm=true to remove this subject and all its grades.')
        try:
            profile = StudentProfile.objects.get(user=request.user)
            ss = StudentSubject.objects.get(pk=pk, student_profile=profile)
        except StudentSubject.DoesNotExist:
            return _error('Subject enrollment not found.', status.HTTP_404_NOT_FOUND)
        ss.delete()
        return _success(message='Subject and all grades removed.')


class CBCGradeListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def _get_student_subject(self, pk, user):
        profile = StudentProfile.objects.get(user=user)
        return StudentSubject.objects.get(pk=pk, student_profile=profile)

    def get(self, request, subject_pk):
        try:
            ss = self._get_student_subject(subject_pk, request.user)
        except StudentSubject.DoesNotExist:
            return _error('Subject enrollment not found.', status.HTTP_404_NOT_FOUND)
        grades = CBCGrade.objects.filter(student_subject=ss)
        return _success(data=CBCGradeSerializer(grades, many=True).data)

    def post(self, request, subject_pk):
        try:
            ss = self._get_student_subject(subject_pk, request.user)
        except StudentSubject.DoesNotExist:
            return _error('Subject enrollment not found.', status.HTTP_404_NOT_FOUND)
        serializer = CBCGradeSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)
        if CBCGrade.objects.filter(
            student_subject=ss,
            term=serializer.validated_data['term'],
            year=serializer.validated_data['year'],
        ).exists():
            return _error('A grade for this subject, term, and year already exists.')
        grade = serializer.save(student_subject=ss)
        return _success(
            data=CBCGradeSerializer(grade).data,
            message='Grade added.',
            status_code=status.HTTP_201_CREATED,
        )


class CBCGradeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def _get_grade(self, subject_pk, grade_pk, user):
        profile = StudentProfile.objects.get(user=user)
        ss = StudentSubject.objects.get(pk=subject_pk, student_profile=profile)
        return CBCGrade.objects.get(pk=grade_pk, student_subject=ss)

    def put(self, request, subject_pk, grade_pk):
        try:
            grade = self._get_grade(subject_pk, grade_pk, request.user)
        except (StudentSubject.DoesNotExist, CBCGrade.DoesNotExist):
            return _error('Grade not found.', status.HTTP_404_NOT_FOUND)
        serializer = CBCGradeSerializer(grade, data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)
        new_term = serializer.validated_data.get('term', grade.term)
        new_year = serializer.validated_data.get('year', grade.year)
        if CBCGrade.objects.filter(
            student_subject=grade.student_subject, term=new_term, year=new_year
        ).exclude(pk=grade.pk).exists():
            return _error('A grade for this subject, term, and year already exists.')
        serializer.save()
        return _success(data=serializer.data, message='Grade updated.')

    def delete(self, request, subject_pk, grade_pk):
        try:
            grade = self._get_grade(subject_pk, grade_pk, request.user)
        except (StudentSubject.DoesNotExist, CBCGrade.DoesNotExist):
            return _error('Grade not found.', status.HTTP_404_NOT_FOUND)
        grade.delete()
        return _success(message='Grade deleted.')


class StudentCounselorView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        from counselors.models import CounselorAssignment
        try:
            profile = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return _success(data=None)
        try:
            assignment = CounselorAssignment.objects.select_related('counselor').get(
                student_profile=profile, is_active=True,
            )
            counselor = assignment.counselor
            data = {
                'id': counselor.id,
                'first_name': counselor.first_name,
                'last_name': counselor.last_name,
                'email': counselor.email,
                'county': counselor.county,
                'photo_url': None,
                'last_message': None,
                'last_message_at': None,
            }
        except CounselorAssignment.DoesNotExist:
            data = None
        return _success(data=data)
