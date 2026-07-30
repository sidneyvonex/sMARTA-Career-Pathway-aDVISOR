from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from accounts.permissions import IsParent, IsEmailVerified, IsStudent
from accounts.response import _success, _error
from accounts.models import StudentProfile
from counselors.models import CounselorAssignment
from parents.models import ParentStudentLink
from parents.serializers import (
    ChildDetailSerializer,
    LinkedChildSerializer,
    ParentAccessSerializer,
)


class ParentChildrenView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsParent]

    def get(self, request):
        links = (
            ParentStudentLink.objects
            .filter(
                parent=request.user,
                status=ParentStudentLink.STATUS_ACTIVE,
            )
            .select_related(
                'student__student_profile__learner_plan'
                '__provisional_choice__combination__track__pathway',
            )
            .prefetch_related(
                'student__student_profile__enrolled_subjects__grades',
                'student__student_profile__riasec_assessments'
                '__recommendations__pathway',
                'student__student_profile__combination_choices'
                '__combination__track__pathway',
                'student__student_profile__learner_plan__milestones',
                Prefetch(
                    'student__student_profile__counselor_assignments',
                    queryset=CounselorAssignment.objects.filter(is_active=True),
                    to_attr='active_parent_assignments',
                ),
            )
        )
        data = LinkedChildSerializer(links, many=True).data
        return _success(data=data)


class ParentChildDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsParent]

    def get(self, request, student_id):
        if not ParentStudentLink.objects.filter(
            parent=request.user,
            student_id=student_id,
            status=ParentStudentLink.STATUS_ACTIVE,
        ).exists():
            return _error('Child not found.', status.HTTP_404_NOT_FOUND)

        try:
            profile = StudentProfile.objects.select_related('user').get(user_id=student_id)
        except StudentProfile.DoesNotExist:
            return _error('Student profile not found.', status.HTTP_404_NOT_FOUND)

        data = ChildDetailSerializer(profile).data
        return _success(data=data)


class StudentParentAccessListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        links = (
            ParentStudentLink.objects
            .filter(student=request.user)
            .select_related('parent')
            .order_by('-created_at')
        )
        return _success(data=ParentAccessSerializer(links, many=True).data)


class StudentParentAccessApproveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def put(self, request, link_id):
        with transaction.atomic():
            link = (
                ParentStudentLink.objects
                .select_for_update()
                .select_related('parent')
                .filter(pk=link_id, student=request.user)
                .first()
            )
            if link is None:
                return _error('Parent access request not found.', status.HTTP_404_NOT_FOUND)
            if link.status == ParentStudentLink.STATUS_REVOKED:
                return _error('A revoked request cannot be approved. Send a new invitation.')
            if link.status != ParentStudentLink.STATUS_ACTIVE:
                link.status = ParentStudentLink.STATUS_ACTIVE
                link.learner_approved_at = timezone.now()
                link.revoked_at = None
                link.save(update_fields=[
                    'status',
                    'learner_approved_at',
                    'revoked_at',
                ])
        return _success(
            data=ParentAccessSerializer(link).data,
            message='Parent access approved.',
        )


class StudentParentAccessRevokeView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def put(self, request, link_id):
        with transaction.atomic():
            link = (
                ParentStudentLink.objects
                .select_for_update()
                .select_related('parent')
                .filter(pk=link_id, student=request.user)
                .first()
            )
            if link is None:
                return _error('Parent access request not found.', status.HTTP_404_NOT_FOUND)
            if link.status != ParentStudentLink.STATUS_REVOKED:
                link.status = ParentStudentLink.STATUS_REVOKED
                link.revoked_at = timezone.now()
                link.save(update_fields=['status', 'revoked_at'])
        return _success(
            data=ParentAccessSerializer(link).data,
            message='Parent access revoked.',
        )
