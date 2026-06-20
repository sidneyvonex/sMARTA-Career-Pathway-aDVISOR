import logging
from datetime import date

from django.conf import settings
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User, StudentProfile
from accounts.permissions import IsEmailVerified
from accounts.response import _error
from counselors.models import CounselorAssignment
from parents.models import ParentStudentLink
from students.models import StudentSubject, GRADE_LEVEL_CHOICES
from riasec.models import RIASECAssessment
from .pdf_builder import build_student_report

logger = logging.getLogger(__name__)

GRADE_LABELS = dict(GRADE_LEVEL_CHOICES)


class StudentReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request, student_id):
        try:
            student = User.objects.get(pk=student_id, role='student')
        except (User.DoesNotExist, ValueError):
            return _error('Student not found.', 404)

        try:
            profile = StudentProfile.objects.select_related('school').get(user=student)
        except StudentProfile.DoesNotExist:
            return _error('Student profile not found.', 404)

        if not self._has_access(request.user, student, profile):
            return _error("You don't have permission to do that.", 403)

        subjects_data = self._get_subjects_data(profile)
        riasec_data, recommendations_data = self._get_riasec_data(profile)

        if not subjects_data and riasec_data is None:
            return _error('This student has no grades or assessment results to report.')

        logo_path = getattr(settings, 'REPORT_LOGO_PATH', None)
        if logo_path:
            logo_path = str(logo_path)

        data = {
            'student_name': f'{student.first_name} {student.last_name}'.strip(),
            'grade': profile.grade,
            'school_name': profile.school.name if profile.school else None,
            'county': (student.county or '').replace('_', ' ').title() if student.county else None,
            'email': student.email,
            'mode': profile.mode,
            'subjects': subjects_data,
            'riasec': riasec_data,
            'recommendations': recommendations_data,
            'logo_path': logo_path,
        }

        pdf_bytes = build_student_report(data)
        today = date.today().isoformat()
        filename = f'smarta-shauri-report-{student.first_name}-{student.last_name}-{today}.pdf'

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _has_access(self, user, student, profile):
        if user.role == 'system_admin':
            return True
        if user.role == 'student':
            return user.id == student.id
        if user.role == 'counselor':
            return CounselorAssignment.objects.filter(
                counselor=user, student_profile=profile, is_active=True,
            ).exists()
        if user.role == 'school_admin':
            return (
                profile.mode == 'school_linked'
                and profile.school_id is not None
                and profile.school_id == user.school_id
            )
        if user.role == 'parent':
            return ParentStudentLink.objects.filter(
                parent=user, student=student,
            ).exists()
        return False

    def _get_subjects_data(self, profile):
        enrollments = (
            StudentSubject.objects
            .filter(student_profile=profile)
            .select_related('subject')
            .prefetch_related('grades')
        )
        subjects = []
        for enrollment in enrollments:
            grades = [
                {
                    'term': g.term,
                    'year': g.year,
                    'level': g.level,
                    'label': GRADE_LABELS.get(g.level, g.level),
                }
                for g in enrollment.grades.all()
            ]
            subjects.append({
                'name': enrollment.subject.name,
                'code': enrollment.subject.code,
                'grades': grades,
            })
        return subjects

    def _get_riasec_data(self, profile):
        assessment = (
            RIASECAssessment.objects
            .filter(student_profile=profile)
            .order_by('-submitted_at')
            .first()
        )
        if not assessment:
            return None, []

        scores = {}
        for s in assessment.scores.all():
            scores[s.dimension] = s.raw_score

        holland_dims = sorted(scores.keys(), key=lambda d: scores.get(d, 0), reverse=True)
        holland_code = ''.join(holland_dims[:2]) if len(holland_dims) >= 2 else ''

        riasec_data = {
            'scores': scores,
            'holland_code': holland_code,
        }

        recommendations = []
        for rec in assessment.recommendations.select_related('pathway').all()[:3]:
            recommendations.append({
                'rank': rec.rank,
                'pathway_name': rec.pathway.name,
                'fit_pct': rec.fit_pct,
            })

        return riasec_data, recommendations
