from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCounselor, IsEmailVerified
from accounts.models import StudentProfile
from accounts.response import _success, _error
from guidance.models import LearnerCombinationChoice, LearnerPlan
from riasec.models import RIASECAssessment
from riasec.serializers import AssessmentResultSerializer
from students.serializers import CBCGradeSerializer
from students.role_support import (
    academic_support_context,
    academic_support_enrolments,
)
from system_admin.utils import log_action
from notifications.models import Notification
from parents.models import ParentStudentLink
from .attention import attention_profiles, attention_reasons_for
from .models import CounselorAssignment, CounselorIntervention, CounselorNote
from .serializers import (
    CounselorInterventionCreateSerializer,
    CounselorInterventionSerializer,
    CounselorNoteCreateSerializer,
    CounselorNoteSerializer,
)


def _get_assigned_profiles(counselor):
    return StudentProfile.objects.filter(
        counselor_assignments__counselor=counselor,
        counselor_assignments__is_active=True,
    ).select_related('user', 'school')


class CounselorPlanReviewView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    @transaction.atomic
    def put(self, request, student_id):
        reviewed = request.data.get('reviewed')
        if type(reviewed) is not bool:
            return _error('reviewed must be a boolean.')

        profile = (
            StudentProfile.objects
            .select_for_update()
            .filter(
                user_id=student_id,
                counselor_assignments__counselor=request.user,
                counselor_assignments__is_active=True,
            )
            .first()
        )
        if profile is None:
            return _error(
                'Assigned learner not found.',
                status.HTTP_404_NOT_FOUND,
            )

        plan = (
            LearnerPlan.objects.select_for_update()
            .filter(student_profile=profile)
            .first()
        )
        if plan is None:
            return _error('Learner plan not found.', status.HTTP_404_NOT_FOUND)
        if reviewed and plan.review_status == LearnerPlan.STATUS_DRAFT:
            return _error(
                'The learner must submit the plan for review first.',
                status.HTTP_409_CONFLICT,
            )

        previous_status = plan.review_status
        new_status = (
            LearnerPlan.STATUS_REVIEWED
            if reviewed
            else LearnerPlan.STATUS_READY
        )
        if previous_status != new_status:
            plan.review_status = new_status
            plan.reviewed_at = timezone.now() if reviewed else None
            plan.save(update_fields=[
                'review_status',
                'reviewed_at',
                'updated_at',
            ])
            log_action(
                actor=request.user,
                action='plan_review_status_changed',
                target_type='plan',
                target_id=plan.id,
                details={
                    'student_id': profile.user_id,
                    'previous_status': previous_status,
                    'status': new_status,
                },
                request=request,
            )

        return _success(
            data={
                'id': plan.id,
                'status': plan.review_status,
                'reviewed_at': (
                    plan.reviewed_at.isoformat()
                    if plan.reviewed_at
                    else None
                ),
            },
            message=(
                'Learner plan marked reviewed.'
                if reviewed
                else 'Learner plan reopened for review.'
            ),
        )


class CounselorStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        profiles = attention_profiles(_get_assigned_profiles(request.user))

        data = []
        for profile in profiles:
            top_pathway = None
            quiz_status = 'pending'
            assessments = profile.attention_assessments
            if assessments:
                quiz_status = 'done'
                recs = list(assessments[0].recommendations.all())
                if recs:
                    top_pathway = recs[0].pathway.name
            attention_reasons = attention_reasons_for(profile)

            data.append({
                'id': profile.user.id,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'grade': profile.grade,
                'county': profile.user.county,
                'photo_url': profile.photo_url,
                'top_pathway': top_pathway,
                'quiz_status': quiz_status,
                'needs_attention': bool(attention_reasons),
                'attention_reasons': attention_reasons,
                'last_active': profile.user.last_login.isoformat() if profile.user.last_login else None,
            })
        return _success(data=data)


class CounselorStudentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request, student_id):
        try:
            profile = attention_profiles(
                _get_assigned_profiles(request.user)
            ).get(user_id=student_id)
        except StudentProfile.DoesNotExist:
            return _error('Student not found.', status.HTTP_404_NOT_FOUND)

        student_data = {
            'id': profile.user.id,
            'email': profile.user.email,
            'first_name': profile.user.first_name,
            'last_name': profile.user.last_name,
            'grade': profile.grade,
            'county': profile.user.county,
            'school': profile.school.name if profile.school else None,
            'photo_url': profile.photo_url,
            'bio': profile.bio,
            'career_interests': profile.career_interests,
            'created_at': profile.user.created_at.isoformat(),
        }

        latest_assessment = (
            profile.riasec_assessments
            .prefetch_related('scores', 'recommendations__pathway')
            .order_by('-submitted_at')
            .first()
        )
        riasec_result = None
        if latest_assessment:
            riasec_result = AssessmentResultSerializer(latest_assessment).data

        support_enrolments = academic_support_enrolments(profile)
        grades = [
            {
                'subject_name': enrollment.subject.name,
                'subject_code': enrollment.subject.code,
                **CBCGradeSerializer(g).data,
            }
            for enrollment in support_enrolments
            for g in enrollment.grades.all()
        ]

        notes_count = CounselorNote.objects.filter(
            counselor=request.user, student_id=student_id, deleted_at__isnull=True,
        ).count()
        academic_subjects = profile.attention_subjects
        subjects_with_evidence = sum(
            bool(subject.attention_grades) for subject in academic_subjects
        )
        total_grade_records = sum(
            len(subject.attention_grades) for subject in academic_subjects
        )
        if (
            len(academic_subjects) >= 3
            and subjects_with_evidence == len(academic_subjects)
        ):
            academic_status = 'ready'
        elif academic_subjects or total_grade_records:
            academic_status = 'in_progress'
        else:
            academic_status = 'not_started'

        choices = (
            LearnerCombinationChoice.objects
            .filter(student_profile=profile)
            .select_related(
                'combination__track__pathway',
                'combination__subject_one',
                'combination__subject_two',
                'combination__subject_three',
            )
        )
        choice_data = [
            {
                'id': choice.id,
                'status': choice.status,
                'learner_reason': choice.learner_reason,
                'code': choice.combination.code,
                'title': choice.combination.title,
                'pathway': choice.combination.track.pathway.name,
                'track': choice.combination.track.name,
                'subjects': [
                    choice.combination.subject_one.name,
                    choice.combination.subject_two.name,
                    choice.combination.subject_three.name,
                ],
            }
            for choice in choices
        ]
        plan = (
            LearnerPlan.objects
            .filter(student_profile=profile)
            .prefetch_related('milestones')
            .first()
        )
        plan_data = None
        if plan is not None:
            plan_data = {
                'status': plan.review_status,
                'learner_reason': plan.learner_reason,
                'milestones': [
                    {
                        'id': milestone.id,
                        'title': milestone.title,
                        'due_date': (
                            milestone.due_date.isoformat()
                            if milestone.due_date
                            else None
                        ),
                        'is_complete': milestone.is_complete,
                    }
                    for milestone in plan.milestones.all()
                ],
            }
        interventions = CounselorIntervention.objects.filter(
            counselor=request.user,
            student_id=student_id,
        ).select_related('student')

        support_context = academic_support_context(
            profile,
            enrolments=support_enrolments,
        )
        return _success(data={
            'student': student_data,
            'riasec_result': riasec_result,
            'grades': grades,
            'notes_count': notes_count,
            'attention_reasons': attention_reasons_for(profile),
            'evidence_summary': {
                'academic': {
                    'status': academic_status,
                    'total_subjects': len(academic_subjects),
                    'subjects_with_evidence': subjects_with_evidence,
                    'total_grade_records': total_grade_records,
                },
                'assessment': {
                    'status': (
                        'complete'
                        if profile.attention_assessments
                        else 'not_started'
                    ),
                },
            },
            'combination_choices': choice_data,
            'plan': plan_data,
            'interventions': CounselorInterventionSerializer(
                interventions,
                many=True,
            ).data,
            **support_context,
        })


class CounselorStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        profiles = list(
            attention_profiles(_get_assigned_profiles(request.user))
        )
        total = len(profiles)
        assessed = sum(
            bool(profile.attention_assessments) for profile in profiles
        )
        needing_attention = sum(
            bool(attention_reasons_for(profile)) for profile in profiles
        )
        journeys_reviewed = sum(
            getattr(profile, 'learner_plan', None) is not None
            and profile.learner_plan.review_status == 'reviewed'
            for profile in profiles
        )
        notes = CounselorNote.objects.filter(
            counselor=request.user, deleted_at__isnull=True,
        ).count()
        follow_ups_due = CounselorIntervention.objects.filter(
            counselor=request.user,
            status=CounselorIntervention.STATUS_OPEN,
            follow_up_date__lte=timezone.localdate(),
        ).count()

        return _success(data={
            'total_students': total,
            'assessments_done': assessed,
            'students_needing_attention': needing_attention,
            'follow_ups_due': follow_ups_due,
            'journeys_reviewed': journeys_reviewed,
            'notes_written': notes,
        })


class CounselorNotesView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        notes = CounselorNote.objects.filter(
            counselor=request.user, deleted_at__isnull=True,
        ).select_related('student')
        return _success(data=CounselorNoteSerializer(notes, many=True).data)

    def post(self, request):
        serializer = CounselorNoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)

        student_id = serializer.validated_data['student_id']
        if not CounselorAssignment.objects.filter(
            counselor=request.user, student_profile__user_id=student_id, is_active=True,
        ).exists():
            return _error('You can only write notes for your assigned students.')

        note = CounselorNote.objects.create(
            counselor=request.user,
            student_id=student_id,
            body=serializer.validated_data['body'],
            visible_to_parent=serializer.validated_data.get('visible_to_parent', False),
        )
        return _success(
            data=CounselorNoteSerializer(note).data,
            message=f'Note saved for {note.student.first_name}.',
            status_code=status.HTTP_201_CREATED,
        )


class CounselorNoteDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def _get_note(self, note_id, user):
        return CounselorNote.objects.get(
            pk=note_id, counselor=user, deleted_at__isnull=True,
        )

    def patch(self, request, note_id):
        try:
            note = self._get_note(note_id, request.user)
        except CounselorNote.DoesNotExist:
            return _error('Note not found.', status.HTTP_404_NOT_FOUND)

        body = request.data.get('body')
        visible_to_parent = request.data.get('visible_to_parent')

        if body is None and visible_to_parent is None:
            return _error('Nothing to update.')

        update_fields = ['updated_at']

        if body is not None:
            if not body:
                return _error('Body is required.')
            if len(body) > 2000:
                return _error('Body must be 2000 characters or less.')
            note.body = body
            update_fields.append('body')

        if visible_to_parent is not None:
            if not isinstance(visible_to_parent, bool):
                return _error('visible_to_parent must be true or false.')
            note.visible_to_parent = visible_to_parent
            update_fields.append('visible_to_parent')

        note.save(update_fields=update_fields)
        return _success(data=CounselorNoteSerializer(note).data, message='Note updated.')

    def delete(self, request, note_id):
        try:
            note = self._get_note(note_id, request.user)
        except CounselorNote.DoesNotExist:
            return _error('Note not found.', status.HTTP_404_NOT_FOUND)
        note.deleted_at = timezone.now()
        note.save(update_fields=['deleted_at'])
        return _success(message='Note removed.')


class CounselorInterventionsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        interventions = CounselorIntervention.objects.filter(
            counselor=request.user,
        ).select_related('student')
        return _success(
            data=CounselorInterventionSerializer(
                interventions,
                many=True,
            ).data
        )

    @transaction.atomic
    def post(self, request):
        serializer = CounselorInterventionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return _error(serializer.errors)

        student_id = serializer.validated_data.pop('student_id')
        if not CounselorAssignment.objects.filter(
            counselor=request.user,
            student_profile__user_id=student_id,
            is_active=True,
        ).exists():
            return _error(
                'You can only create interventions for your assigned students.'
            )

        intervention = CounselorIntervention.objects.create(
            counselor=request.user,
            student_id=student_id,
            **serializer.validated_data,
        )
        if intervention.learner_visible:
            Notification.objects.create(
                user=intervention.student,
                type='counselor_intervention',
                message='Your counsellor recorded a new support action.',
            )
        if intervention.parent_visible:
            parent_ids = ParentStudentLink.objects.filter(
                student=intervention.student,
                status=ParentStudentLink.STATUS_ACTIVE,
            ).values_list('parent_id', flat=True)
            for parent_id in parent_ids:
                Notification.objects.create(
                    user_id=parent_id,
                    type='counselor_intervention',
                    message=(
                        'A learner-approved support action is available for '
                        f'{intervention.student.first_name}.'
                    ),
                )
        return _success(
            data=CounselorInterventionSerializer(intervention).data,
            message='Intervention saved.',
            status_code=status.HTTP_201_CREATED,
        )


class CounselorInterventionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    @transaction.atomic
    def patch(self, request, intervention_id):
        try:
            intervention = (
                CounselorIntervention.objects
                .select_for_update()
                .select_related('student')
                .get(pk=intervention_id, counselor=request.user)
            )
        except CounselorIntervention.DoesNotExist:
            return _error('Intervention not found.', status.HTTP_404_NOT_FOUND)

        was_learner_visible = intervention.learner_visible
        was_parent_visible = intervention.parent_visible
        serializer = CounselorInterventionSerializer(
            intervention,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return _error(serializer.errors)
        intervention = serializer.save()

        if not was_learner_visible and intervention.learner_visible:
            Notification.objects.create(
                user=intervention.student,
                type='counselor_intervention',
                message='Your counsellor recorded a new support action.',
            )
        if not was_parent_visible and intervention.parent_visible:
            parent_ids = (
                ParentStudentLink.objects
                .filter(
                    student=intervention.student,
                    status=ParentStudentLink.STATUS_ACTIVE,
                )
                .values_list('parent_id', flat=True)
                .distinct()
            )
            Notification.objects.bulk_create([
                Notification(
                    user_id=parent_id,
                    type='counselor_intervention',
                    message=(
                        'A learner-approved support action is available for '
                        f'{intervention.student.first_name}.'
                    ),
                )
                for parent_id in parent_ids
            ])
        return _success(
            data=CounselorInterventionSerializer(intervention).data,
            message='Intervention updated.',
        )
