from io import BytesIO
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch, Q
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from PIL import Image
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsStudent, IsEmailVerified
from accounts.models import StudentProfile, StudentSchoolMembership
from accounts.serializers import (
    StudentSchoolMembershipRequestSerializer,
    StudentSchoolMembershipSerializer,
)
from accounts.response import _success, _error
from guidance.models import (
    FrameworkVersion,
    LearnerCombinationChoice,
    LearnerPlan,
    PlanMilestone,
    SchoolOffering,
)
from counselors.models import CounselorIntervention
from counselors.serializers import CounselorInterventionSerializer
from system_admin.utils import log_action
from guidance.selectors import active_combination_queryset
from guidance.serializers import (
    LearnerCombinationChoiceCreateSerializer,
    LearnerCombinationChoiceSerializer,
    LearnerPlanSerializer,
    LearnerPlanUpdateSerializer,
    PlanMilestoneSerializer,
)
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from riasec.models import RIASECAssessment
from riasec.serializers import AssessmentResultSerializer
from counselors.models import CounselorAssignment
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


def learner_plan_queryset(profile):
    active_offerings = (
        SchoolOffering.objects
        .filter(is_active=True, school__is_active=True)
        .select_related('school')
        .order_by('school__name')
    )
    return (
        LearnerPlan.objects
        .filter(student_profile=profile)
        .select_related(
            'provisional_choice__combination__framework_version',
            'provisional_choice__combination__track__pathway',
            'provisional_choice__combination__subject_one',
            'provisional_choice__combination__subject_two',
            'provisional_choice__combination__subject_three',
        )
        .prefetch_related(
            'milestones',
            Prefetch(
                'provisional_choice__combination__school_offerings',
                queryset=active_offerings,
                to_attr='active_school_offerings',
            ),
        )
    )


class EvidenceSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = (
            StudentProfile.objects
            .select_related('learner_plan')
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
        try:
            plan_status = profile.learner_plan.review_status
        except LearnerPlan.DoesNotExist:
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


class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = (
            StudentProfile.objects
            .select_related('user', 'school', 'learner_plan')
            .annotate(
                saved_combination_count=Count(
                    'combination_choices',
                    distinct=True,
                ),
                provisional_combination_count=Count(
                    'combination_choices',
                    filter=Q(
                        combination_choices__status=(
                            LearnerCombinationChoice.STATUS_PROVISIONAL
                        )
                    ),
                    distinct=True,
                ),
            )
            .get(user=request.user)
        )
        grades = grade_summary(profile)
        academic_evidence = {
            key: grades[key]
            for key in (
                'status',
                'total_subjects',
                'subjects_with_evidence',
                'total_grade_records',
            )
        }
        assessment = (
            RIASECAssessment.objects
            .filter(student_profile=profile)
            .prefetch_related('scores', 'recommendations__pathway')
            .order_by('-submitted_at', '-pk')
            .first()
        )
        assessment_evidence = (
            {
                'status': 'complete',
                'instrument_version': assessment.instrument_version,
                'submitted_at': assessment.submitted_at.isoformat(),
            }
            if assessment else {
                'status': 'not_started',
                'instrument_version': None,
                'submitted_at': None,
            }
        )
        profile_completion = profile_completion_summary(profile)
        try:
            plan_status = profile.learner_plan.review_status
        except LearnerPlan.DoesNotExist:
            plan_status = 'not_started'
        has_provisional_choice = profile.provisional_combination_count > 0
        evidence = {
            'profile_completion': profile_completion,
            'academic_evidence': academic_evidence,
            'assessment': assessment_evidence,
            'saved_combination_count': profile.saved_combination_count,
            'plan_status': plan_status,
            'next_action': next_action_for(
                profile_completion,
                academic_evidence,
                assessment_evidence,
                profile.saved_combination_count,
                has_provisional_choice=has_provisional_choice,
                plan_status=plan_status,
            ),
        }

        assignment = (
            CounselorAssignment.objects
            .filter(student_profile=profile, is_active=True)
            .select_related('counselor')
            .first()
        )
        counselor = None
        if assignment:
            user = assignment.counselor
            counselor = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'county': user.county,
                'photo_url': None,
                'last_message': None,
                'last_message_at': None,
            }

        notifications = (
            Notification.objects
            .filter(user=request.user)
            .order_by('-created_at')[:50]
        )
        interventions = (
            CounselorIntervention.objects
            .filter(student=request.user, learner_visible=True)
            .select_related('student')
        )
        return _success(data={
            'profile': StudentProfileSerializer(profile).data,
            'grade_summary': grades,
            'evidence': evidence,
            'choices': LearnerCombinationChoiceSerializer(
                learner_choice_queryset(profile),
                many=True,
            ).data,
            'assessment': (
                AssessmentResultSerializer(assessment).data
                if assessment else None
            ),
            'counselor': counselor,
            'notifications': NotificationSerializer(
                notifications,
                many=True,
            ).data,
            'interventions': CounselorInterventionSerializer(
                interventions,
                many=True,
            ).data,
        })


class StudentInterventionsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        interventions = CounselorIntervention.objects.filter(
            student=request.user,
            learner_visible=True,
        ).select_related('student')
        return _success(
            data=CounselorInterventionSerializer(
                interventions,
                many=True,
            ).data
        )


class StudentSchoolMembershipListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        memberships = (
            StudentSchoolMembership.objects
            .filter(student_profile__user=request.user)
            .select_related('school')
        )
        return _success(
            data=StudentSchoolMembershipSerializer(
                memberships,
                many=True,
            ).data
        )

    def post(self, request):
        serializer = StudentSchoolMembershipRequestSerializer(
            data=request.data,
            context={},
        )
        if not serializer.is_valid():
            return _error(serializer.errors)
        target_school = serializer.context['target_school']

        with transaction.atomic():
            profile = (
                StudentProfile.objects.select_for_update()
                .select_related('school')
                .get(user=request.user)
            )
            memberships = StudentSchoolMembership.objects.select_for_update().filter(
                student_profile=profile,
            )
            if memberships.filter(status='pending').exists():
                return _error(
                    'A school membership request is already pending.',
                    status.HTTP_409_CONFLICT,
                )
            active = memberships.filter(status='active').first()
            legacy_active_school_id = (
                profile.school_id
                if (
                    active is None
                    and not memberships.exists()
                    and profile.school_id is not None
                    and profile.mode == 'school_linked'
                    and profile.school_membership_status == 'active'
                )
                else None
            )
            if (
                (active is not None and active.school_id == target_school.pk)
                or (
                    legacy_active_school_id == target_school.pk
                )
            ):
                return _error('You are already an active member of this school.')

            if legacy_active_school_id is not None:
                active = StudentSchoolMembership.objects.create(
                    student_profile=profile,
                    school_id=legacy_active_school_id,
                    status=StudentSchoolMembership.STATUS_ACTIVE,
                    record_source=(
                        StudentSchoolMembership.SOURCE_LEGACY_BACKFILL
                    ),
                    requested_at=None,
                    started_at=None,
                )

            try:
                membership = StudentSchoolMembership.objects.create(
                    student_profile=profile,
                    school=target_school,
                    status=StudentSchoolMembership.STATUS_PENDING,
                    record_source=(
                        StudentSchoolMembership.SOURCE_LEARNER_REQUEST
                    ),
                    requested_at=timezone.now(),
                )
            except IntegrityError:
                return _error(
                    'A school membership request is already pending.',
                    status.HTTP_409_CONFLICT,
                )

            if active is None:
                profile.mode = 'school_linked'
                profile.school = target_school
                profile.school_membership_status = 'pending'
                profile.save(
                    update_fields=[
                        'mode',
                        'school',
                        'school_membership_status',
                    ]
                )

        membership = StudentSchoolMembership.objects.select_related('school').get(
            pk=membership.pk
        )
        return _success(
            data=StudentSchoolMembershipSerializer(membership).data,
            message='School membership request submitted.',
            status_code=status.HTTP_201_CREATED,
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
        if choice.plans.exists():
            return _error('This combination is still linked to your learner plan.')
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
            previous_choice_id = (
                LearnerCombinationChoice.objects
                .filter(
                    student_profile=profile,
                    status=LearnerCombinationChoice.STATUS_PROVISIONAL,
                )
                .exclude(pk=choice.pk)
                .values_list('pk', flat=True)
                .first()
            )
            status_changed = (
                choice.status != LearnerCombinationChoice.STATUS_PROVISIONAL
                or previous_choice_id is not None
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
            LearnerPlan.objects.filter(student_profile=profile).update(
                provisional_choice=choice,
                review_status=LearnerPlan.STATUS_DRAFT,
                reviewed_at=None,
            )
            if status_changed:
                log_action(
                    actor=request.user,
                    action='provisional_combination_changed',
                    target_type='choice',
                    target_id=choice.id,
                    details={
                        'previous_choice_id': previous_choice_id,
                        'choice_id': choice.id,
                        'combination_id': choice.combination_id,
                    },
                    request=request,
                )

        return _success(
            data=LearnerCombinationChoiceSerializer(choice).data,
            message='Provisional combination updated.',
        )


class LearnerPlanView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        plan = learner_plan_queryset(profile).first()
        return _success(
            data=LearnerPlanSerializer(plan).data if plan else None
        )

    def put(self, request):
        serializer = LearnerPlanUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)

        with transaction.atomic():
            profile = StudentProfile.objects.select_for_update().get(
                user=request.user
            )
            provisional_choice = (
                LearnerCombinationChoice.objects
                .select_for_update()
                .filter(
                    student_profile=profile,
                    status=LearnerCombinationChoice.STATUS_PROVISIONAL,
                )
                .first()
            )
            if provisional_choice is None:
                return _error(
                    'Choose a provisional combination before creating a plan.'
                )

            plan, created = LearnerPlan.objects.select_for_update().get_or_create(
                student_profile=profile,
                defaults={'provisional_choice': provisional_choice},
            )
            changed_fields = []
            if plan.provisional_choice_id != provisional_choice.pk:
                plan.provisional_choice = provisional_choice
                plan.review_status = LearnerPlan.STATUS_DRAFT
                plan.reviewed_at = None
                changed_fields.extend([
                    'provisional_choice',
                    'review_status',
                    'reviewed_at',
                ])

            for field_name in ('learner_reason', 'review_status'):
                if field_name in serializer.validated_data:
                    value = serializer.validated_data[field_name]
                    if getattr(plan, field_name) != value:
                        setattr(plan, field_name, value)
                        changed_fields.append(field_name)

            reason_changed = 'learner_reason' in changed_fields
            status_was_explicit = 'review_status' in serializer.validated_data
            if (
                reason_changed
                and not status_was_explicit
                and plan.review_status == LearnerPlan.STATUS_REVIEWED
            ):
                plan.review_status = LearnerPlan.STATUS_DRAFT
                plan.reviewed_at = None
                changed_fields.extend(['review_status', 'reviewed_at'])

            if plan.review_status != LearnerPlan.STATUS_REVIEWED and plan.reviewed_at:
                plan.reviewed_at = None
                changed_fields.append('reviewed_at')
            if changed_fields:
                plan.save(update_fields=[*set(changed_fields), 'updated_at'])

        plan = learner_plan_queryset(profile).get(pk=plan.pk)
        return _success(
            data=LearnerPlanSerializer(plan).data,
            message='Learner plan created.' if created else 'Learner plan updated.',
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PlanMilestoneListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def post(self, request):
        profile = StudentProfile.objects.get(user=request.user)
        plan = get_object_or_404(LearnerPlan, student_profile=profile)
        serializer = PlanMilestoneSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)
        is_complete = serializer.validated_data.get('is_complete', False)
        milestone = serializer.save(
            plan=plan,
            completed_at=timezone.now() if is_complete else None,
        )
        return _success(
            data=PlanMilestoneSerializer(milestone).data,
            message='Milestone added.',
            status_code=status.HTTP_201_CREATED,
        )


class PlanMilestoneDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def put(self, request, milestone_id):
        profile = StudentProfile.objects.get(user=request.user)
        milestone = get_object_or_404(
            PlanMilestone,
            pk=milestone_id,
            plan__student_profile=profile,
        )
        serializer = PlanMilestoneSerializer(
            milestone,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return _error(serializer.errors)
        complete_before = milestone.is_complete
        complete_after = serializer.validated_data.get(
            'is_complete',
            complete_before,
        )
        serializer.save(
            completed_at=(
                timezone.now()
                if complete_after and not complete_before
                else None if not complete_after else milestone.completed_at
            )
        )
        return _success(
            data=serializer.data,
            message='Milestone updated.',
        )

    def delete(self, request, milestone_id):
        profile = StudentProfile.objects.get(user=request.user)
        milestone = get_object_or_404(
            PlanMilestone,
            pk=milestone_id,
            plan__student_profile=profile,
        )
        milestone.delete()
        return _success(
            message='Milestone removed.',
            status_code=status.HTTP_204_NO_CONTENT,
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
        if request.query_params.get('include_history') != 'true':
            qs = qs.filter(is_active=True)
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
        duplicate_message = (
            f'You are already enrolled in this subject for Grade {subject.grade}.'
        )
        if StudentSubject.objects.filter(
            student_profile=profile,
            continuity_code=subject.continuity_code,
            academic_grade=subject.grade,
            is_active=True,
        ).exists():
            return _error(duplicate_message)
        try:
            with transaction.atomic():
                ss = StudentSubject.objects.create(
                    student_profile=profile,
                    subject=subject,
                )
        except IntegrityError:
            return _error(duplicate_message)
        return _success(
            data=StudentSubjectSerializer(ss).data,
            message='Subject added.',
            status_code=status.HTTP_201_CREATED,
        )


class MySubjectRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def post(self, request, pk):
        if not request.data.get('confirm'):
            return _error('Set confirm=true to remove this subject.')
        try:
            profile = StudentProfile.objects.get(user=request.user)
            ss = StudentSubject.objects.get(
                pk=pk,
                student_profile=profile,
                is_active=True,
            )
        except StudentSubject.DoesNotExist:
            return _error('Subject enrollment not found.', status.HTTP_404_NOT_FOUND)
        ss.archive()
        return _success(message='Subject removed.')


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
        if not ss.is_active:
            return _error(
                'Grades cannot be changed on an archived subject enrollment.'
            )
        serializer = CBCGradeSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)
        if CBCGrade.objects.filter(
            student_subject=ss,
            term=serializer.validated_data['term'],
            year=serializer.validated_data['year'],
        ).exists():
            return _error('A grade for this subject, term, and year already exists.')
        grade = serializer.save(
            student_subject=ss,
            academic_grade=ss.academic_grade,
        )
        return _success(
            data=CBCGradeSerializer(grade).data,
            message='Grade added.',
            status_code=status.HTTP_201_CREATED,
        )


class CBCGradeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def _get_grade(self, subject_pk, grade_pk, user):
        profile = StudentProfile.objects.get(user=user)
        ss = StudentSubject.objects.select_for_update().get(
            pk=subject_pk,
            student_profile=profile,
        )
        return CBCGrade.objects.select_for_update().get(
            pk=grade_pk,
            student_subject=ss,
        )

    def put(self, request, subject_pk, grade_pk):
        with transaction.atomic():
            try:
                grade = self._get_grade(subject_pk, grade_pk, request.user)
            except (StudentSubject.DoesNotExist, CBCGrade.DoesNotExist):
                return _error('Grade not found.', status.HTTP_404_NOT_FOUND)
            if not grade.student_subject.is_active:
                return _error(
                    'Grades cannot be changed on an archived subject enrollment.'
                )
            if any((
                grade.verified_school_id,
                grade.verified_by_id,
                grade.verified_at,
            )):
                return _error(
                    'School-verified evidence cannot be edited by a learner.',
                    status.HTTP_403_FORBIDDEN,
                )
            serializer = CBCGradeSerializer(grade, data=request.data)
            if not serializer.is_valid():
                return _error(serializer.errors)
            new_term = serializer.validated_data.get('term', grade.term)
            new_year = serializer.validated_data.get('year', grade.year)
            if CBCGrade.objects.filter(
                student_subject=grade.student_subject,
                term=new_term,
                year=new_year,
            ).exclude(pk=grade.pk).exists():
                return _error(
                    'A grade for this subject, term, and year already exists.'
                )
            serializer.save()
            return _success(data=serializer.data, message='Grade updated.')

    def delete(self, request, subject_pk, grade_pk):
        with transaction.atomic():
            try:
                grade = self._get_grade(subject_pk, grade_pk, request.user)
            except (StudentSubject.DoesNotExist, CBCGrade.DoesNotExist):
                return _error('Grade not found.', status.HTTP_404_NOT_FOUND)
            if not grade.student_subject.is_active:
                return _error(
                    'Grades cannot be changed on an archived subject enrollment.'
                )
            if any((
                grade.verified_school_id,
                grade.verified_by_id,
                grade.verified_at,
            )):
                return _error(
                    'School-verified evidence cannot be deleted by a learner.',
                    status.HTTP_403_FORBIDDEN,
                )
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
