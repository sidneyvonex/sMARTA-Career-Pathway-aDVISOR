from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCounselor, IsEmailVerified
from accounts.models import StudentProfile
from .models import CounselorAssignment, CounselorNote
from .serializers import CounselorNoteSerializer, CounselorNoteCreateSerializer


def _success(data=None, message='', status_code=status.HTTP_200_OK):
    return Response({'data': data, 'error': None, 'message': message}, status=status_code)


def _error(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({'data': None, 'error': True, 'message': message}, status=status_code)


def _get_assigned_profiles(counselor):
    return StudentProfile.objects.filter(
        counselor_assignments__counselor=counselor,
        counselor_assignments__is_active=True,
    ).select_related('user', 'school')


class CounselorStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        profiles = _get_assigned_profiles(request.user)
        data = []
        for profile in profiles:
            latest_assessment = (
                profile.riasec_assessments
                .prefetch_related('recommendations__pathway')
                .order_by('-submitted_at')
                .first()
            )
            top_pathway = None
            fit_pct = None
            quiz_status = 'pending'
            if latest_assessment:
                quiz_status = 'done'
                top_rec = latest_assessment.recommendations.order_by('rank').first()
                if top_rec:
                    top_pathway = top_rec.pathway.name
                    fit_pct = top_rec.fit_pct

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
            from riasec.serializers import AssessmentResultSerializer
            riasec_result = AssessmentResultSerializer(latest_assessment).data

        from students.models import StudentSubject, CBCGrade
        from students.serializers import CBCGradeSerializer
        enrolled = StudentSubject.objects.filter(student_profile=profile).select_related('subject')
        grades = []
        for ss in enrolled:
            for g in CBCGrade.objects.filter(student_subject=ss):
                grades.append({
                    'subject_name': ss.subject.name,
                    'subject_code': ss.subject.code,
                    **CBCGradeSerializer(g).data,
                })

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
        profiles = _get_assigned_profiles(request.user)
        total = profiles.count()
        assessed = sum(
            1 for p in profiles if p.riasec_assessments.exists()
        )
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
