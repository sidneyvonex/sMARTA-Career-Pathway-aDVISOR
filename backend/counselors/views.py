from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCounselor, IsEmailVerified
from accounts.models import StudentProfile
from accounts.response import _success, _error
from riasec.models import RIASECAssessment
from riasec.serializers import AssessmentResultSerializer
from students.models import CBCGrade
from students.serializers import CBCGradeSerializer
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


class CounselorStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        profiles = attention_profiles(_get_assigned_profiles(request.user))

        data = []
        for profile in profiles:
            top_pathway = None
            fit_pct = None
            quiz_status = 'pending'
            assessments = profile.attention_assessments
            if assessments:
                quiz_status = 'done'
                recs = list(assessments[0].recommendations.all())
                if recs:
                    top_pathway = recs[0].pathway.name
                    fit_pct = recs[0].fit_pct
            attention_reasons = attention_reasons_for(profile)

            data.append({
                'id': profile.user.id,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'grade': profile.grade,
                'county': profile.user.county,
                'photo_url': profile.photo_url,
                'top_pathway': top_pathway,
                'fit_pct': fit_pct,
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
            profile = _get_assigned_profiles(request.user).get(user_id=student_id)
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

        grades_qs = CBCGrade.objects.filter(
            student_subject__student_profile=profile,
        ).select_related('student_subject__subject')
        grades = [
            {
                'subject_name': g.student_subject.subject.name,
                'subject_code': g.student_subject.subject.code,
                **CBCGradeSerializer(g).data,
            }
            for g in grades_qs
        ]

        notes_count = CounselorNote.objects.filter(
            counselor=request.user, student_id=student_id, deleted_at__isnull=True,
        ).count()

        return _success(data={
            'student': student_data,
            'riasec_result': riasec_result,
            'grades': grades,
            'notes_count': notes_count,
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
        notes = CounselorNote.objects.filter(
            counselor=request.user, deleted_at__isnull=True,
        ).count()

        return _success(data={
            'total_students': total,
            'assessments_done': assessed,
            'students_needing_attention': needing_attention,
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
        return _success(
            data=CounselorInterventionSerializer(intervention).data,
            message='Intervention saved.',
            status_code=status.HTTP_201_CREATED,
        )


class CounselorInterventionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def patch(self, request, intervention_id):
        try:
            intervention = CounselorIntervention.objects.select_related(
                'student'
            ).get(pk=intervention_id, counselor=request.user)
        except CounselorIntervention.DoesNotExist:
            return _error('Intervention not found.', status.HTTP_404_NOT_FOUND)

        serializer = CounselorInterventionSerializer(
            intervention,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return _error(serializer.errors)
        serializer.save()
        return _success(
            data=CounselorInterventionSerializer(intervention).data,
            message='Intervention updated.',
        )
