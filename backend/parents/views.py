from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from accounts.permissions import IsParent, IsEmailVerified, IsStudent
from accounts.response import _success, _error
from accounts.models import StudentProfile
from counselors.models import (
    CounselorAssignment,
    CounselorIntervention,
    CounselorNote,
)
from guidance.models import LearnerCombinationChoice
from riasec.models import RIASECAssessment
from students.role_support import (
    academic_support_context,
    academic_support_enrolment_queryset,
)
from parents.models import ParentStudentLink
from system_admin.utils import log_action
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
            profile = (
                StudentProfile.objects
                .select_related(
                    'user',
                    'learner_plan__provisional_choice__combination'
                    '__track__pathway',
                    'learner_plan__provisional_choice__combination__subject_one',
                    'learner_plan__provisional_choice__combination__subject_two',
                    'learner_plan__provisional_choice__combination__subject_three',
                )
                .prefetch_related(
                    Prefetch(
                        'enrolled_subjects',
                        queryset=academic_support_enrolment_queryset(),
                        to_attr='support_enrolments',
                    ),
                    Prefetch(
                        'riasec_assessments',
                        queryset=RIASECAssessment.objects
                        .prefetch_related('scores', 'recommendations__pathway')
                        .order_by('-submitted_at'),
                    ),
                    Prefetch(
                        'counselor_assignments',
                        queryset=CounselorAssignment.objects
                        .filter(is_active=True)
                        .select_related('counselor'),
                        to_attr='active_parent_assignments',
                    ),
                    Prefetch(
                        'combination_choices',
                        queryset=LearnerCombinationChoice.objects.select_related(
                            'combination__track__pathway',
                            'combination__subject_one',
                            'combination__subject_two',
                            'combination__subject_three',
                        ),
                    ),
                    'learner_plan__milestones',
                    Prefetch(
                        'user__counselor_notes_received',
                        queryset=CounselorNote.objects.filter(
                            visible_to_parent=True,
                            deleted_at__isnull=True,
                        ).order_by('-created_at'),
                        to_attr='parent_visible_notes',
                    ),
                    Prefetch(
                        'user__counselor_interventions_received',
                        queryset=CounselorIntervention.objects.filter(
                            parent_visible=True,
                        ).select_related('student'),
                        to_attr='parent_visible_interventions',
                    ),
                )
                .get(user_id=student_id)
            )
        except StudentProfile.DoesNotExist:
            return _error('Student profile not found.', status.HTTP_404_NOT_FOUND)

        data = {
            **ChildDetailSerializer(profile).data,
            **academic_support_context(profile),
        }
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
                previous_status = link.status
                link.status = ParentStudentLink.STATUS_ACTIVE
                link.learner_approved_at = timezone.now()
                link.revoked_at = None
                link.save(update_fields=[
                    'status',
                    'learner_approved_at',
                    'revoked_at',
                ])
                log_action(
                    actor=request.user,
                    action='parent_link_approved',
                    target_type='parent_link',
                    target_id=link.id,
                    details={
                        'parent_id': link.parent_id,
                        'previous_status': previous_status,
                        'status': link.status,
                    },
                    request=request,
                )
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
                previous_status = link.status
                link.status = ParentStudentLink.STATUS_REVOKED
                link.revoked_at = timezone.now()
                link.save(update_fields=['status', 'revoked_at'])
                log_action(
                    actor=request.user,
                    action='parent_link_revoked',
                    target_type='parent_link',
                    target_id=link.id,
                    details={
                        'parent_id': link.parent_id,
                        'previous_status': previous_status,
                        'status': link.status,
                    },
                    request=request,
                )
        return _success(
            data=ParentAccessSerializer(link).data,
            message='Parent access revoked.',
        )
