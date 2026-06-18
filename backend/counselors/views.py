from django.db.models import Exists, OuterRef, Prefetch
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCounselor, IsEmailVerified
from accounts.models import StudentProfile
from accounts.response import _success, _error
from riasec.models import RIASECAssessment, Recommendation
from riasec.serializers import AssessmentResultSerializer
from students.models import CBCGrade
from students.serializers import CBCGradeSerializer
from .models import CounselorAssignment, CounselorNote
from .serializers import CounselorNoteSerializer, CounselorNoteCreateSerializer


def _get_assigned_profiles(counselor):
    return StudentProfile.objects.filter(
        counselor_assignments__counselor=counselor,
        counselor_assignments__is_active=True,
    ).select_related('user', 'school')


class CounselorStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        latest_assessments = RIASECAssessment.objects.filter(
            student_profile=OuterRef('pk'),
        ).order_by('-submitted_at')

        profiles = (
            _get_assigned_profiles(request.user)
            .annotate(has_assessment=Exists(latest_assessments))
            .prefetch_related(
                Prefetch(
                    'riasec_assessments',
                    queryset=RIASECAssessment.objects.order_by('-submitted_at').prefetch_related(
                        Prefetch('recommendations', queryset=Recommendation.objects.select_related('pathway').order_by('rank'))
                    ),
                )
            )
        )

        data = []
        for profile in profiles:
            top_pathway = None
            fit_pct = None
            quiz_status = 'pending'

            if profile.has_assessment:
                quiz_status = 'done'
                assessments = list(profile.riasec_assessments.all())
                if assessments:
                    latest = assessments[0]
                    recs = list(latest.recommendations.all())
                    if recs:
                        top_pathway = recs[0].pathway.name
                        fit_pct = recs[0].fit_pct

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
        latest_assessments = RIASECAssessment.objects.filter(
            student_profile=OuterRef('pk'),
        )
        profiles = _get_assigned_profiles(request.user).annotate(
            has_assessment=Exists(latest_assessments),
        )
        total = profiles.count()
        assessed = profiles.filter(has_assessment=True).count()
        notes = CounselorNote.objects.filter(
            counselor=request.user, deleted_at__isnull=True,
        ).count()

        return _success(data={
            'total_students': total,
            'assessments_done': assessed,
            'students_needing_attention': total - assessed,
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
        if not body:
            return _error('Body is required.')
        if len(body) > 2000:
            return _error('Body must be 2000 characters or less.')
        note.body = body
        note.save(update_fields=['body', 'updated_at'])
        return _success(data=CounselorNoteSerializer(note).data, message='Note updated.')

    def delete(self, request, note_id):
        try:
            note = self._get_note(note_id, request.user)
        except CounselorNote.DoesNotExist:
            return _error('Note not found.', status.HTTP_404_NOT_FOUND)
        note.deleted_at = timezone.now()
        note.save(update_fields=['deleted_at'])
        return _success(message='Note removed.')
