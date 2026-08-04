import re
from datetime import date

from django.conf import settings
from django.db.models import Exists, OuterRef, Subquery
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User, StudentProfile, StudentSchoolMembership
from accounts.permissions import IsCounselor, IsEmailVerified, IsSchoolAdmin, IsSystemAdmin
from accounts.response import _error
from counselors.models import CounselorAssignment
from guidance.models import FrameworkVersion, LearnerCombinationChoice, LearnerPlan
from parents.models import ParentStudentLink
from students.role_support import (
    academic_support_context,
    academic_support_enrolments,
)
from riasec.models import RIASECAssessment
from system_admin.utils import log_action
from school_admin.reporting import get_school_roster, get_school_stats
from counselors.reporting import get_caseload_roster, get_caseload_stats
from system_admin.reporting import get_platform_stats, get_schools_directory
from .pdf import (
    build_cohort_overview_report,
    build_cohort_roster_report,
    build_platform_overview_report,
    build_schools_directory_report,
    build_student_report,
)

GRADE_LABELS = dict(StudentProfile.GRADE_CHOICES)


def _logo_path():
    value = getattr(settings, 'REPORT_LOGO_PATH', None)
    return str(value) if value else None


def _grade_filter(request):
    raw_grade = request.query_params.get('grade')
    if raw_grade in (None, ''):
        return None, None
    try:
        grade = int(raw_grade)
    except (TypeError, ValueError):
        return None, _error('Invalid grade filter.', 400)
    if grade not in GRADE_LABELS:
        return None, _error('Invalid grade filter.', 400)
    return grade, None


def _pdf_response(pdf_bytes, filename):
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _safe_scope(value):
    return re.sub(r'[^A-Za-z0-9-]+', '-', str(value)).strip('-').lower() or 'report'


def _percent(value, total):
    return round((value / total) * 100) if total else 0


class StudentReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request, student_id):
        try:
            student = User.objects.get(pk=student_id, role='student')
        except (User.DoesNotExist, ValueError):
            return _error('Student not found.', 404)

        try:
            membership_history = StudentSchoolMembership.objects.filter(
                student_profile=OuterRef('pk'),
            )
            active_membership = membership_history.filter(
                status=StudentSchoolMembership.STATUS_ACTIVE,
            ).order_by('pk')
            profile = (
                StudentProfile.objects
                .select_related('school')
                .annotate(
                    report_has_membership_history=Exists(membership_history),
                    report_active_school_id=Subquery(
                        active_membership.values('school_id')[:1]
                    ),
                    report_active_school_name=Subquery(
                        active_membership.values('school__name')[:1]
                    ),
                    report_active_membership_status=Subquery(
                        active_membership.values('status')[:1]
                    ),
                )
                .get(user=student)
            )
        except StudentProfile.DoesNotExist:
            return _error('Student profile not found.', 404)

        membership_context = self._membership_context(profile)
        if not self._has_access(
            request.user,
            student,
            profile,
            membership_context,
        ):
            return _error("You don't have permission to do that.", 403)

        support_enrolments = academic_support_enrolments(profile)
        subjects_data = self._get_subjects_data(profile, support_enrolments)
        support_context = academic_support_context(
            profile,
            enrolments=support_enrolments,
        )
        riasec_data, recommendations_data = self._get_riasec_data(profile)

        if not subjects_data and riasec_data is None:
            return _error('This student has no grades or assessment results to report.', 400)

        logo_path = getattr(settings, 'REPORT_LOGO_PATH', None)
        if logo_path:
            logo_path = str(logo_path)

        plan, provisional_choice = self._get_plan_context(profile)
        framework = (
            provisional_choice.combination.framework_version
            if provisional_choice
            else FrameworkVersion.objects.current()
        )
        subjects_with_evidence = sum(bool(subject['grades']) for subject in subjects_data)
        total_grade_records = sum(len(subject['grades']) for subject in subjects_data)
        total_subjects = len(subjects_data)
        if total_subjects >= 3 and subjects_with_evidence == total_subjects:
            completeness_status = 'complete'
            completeness_label = 'Complete coverage'
        elif total_subjects or total_grade_records:
            completeness_status = 'in_progress'
            completeness_label = 'In progress'
        else:
            completeness_status = 'not_started'
            completeness_label = 'Not started'

        generated_at = timezone.localtime()
        data = {
            'student_name': f'{student.first_name} {student.last_name}'.strip(),
            'grade': profile.grade,
            'school_name': membership_context['school_name'],
            'school_membership_status': membership_context['status'],
            'county': (student.county or '').replace('_', ' ').title() if student.county else None,
            'email': student.email,
            'mode': profile.mode,
            'subjects': subjects_data,
            'riasec': riasec_data,
            'recommendations': recommendations_data,
            'evidence_summary': {
                'subjects_with_evidence': subjects_with_evidence,
                'total_subjects': total_subjects,
                'total_grade_records': total_grade_records,
                'assessment_submitted_at': (
                    riasec_data['submitted_at'] if riasec_data else None
                ),
            },
            'evidence_completeness': {
                'status': completeness_status,
                'label': completeness_label,
                'explanation': (
                    f'{subjects_with_evidence} of {total_subjects} enrolled subjects '
                    'have recorded academic evidence.'
                ),
            },
            **support_context,
            'provisional_choice': self._serialize_choice(provisional_choice),
            'plan': self._serialize_plan(plan),
            'framework': (
                {
                    'code': framework.code,
                    'title': framework.title,
                    'effective_date': framework.effective_date.strftime('%d %B %Y'),
                    'source_url': framework.source_url,
                }
                if framework else None
            ),
            'instrument_version': (
                riasec_data.get('instrument_version') if riasec_data else None
            ),
            'algorithm_version': (
                next(
                    (
                        recommendation.get('algorithm_version')
                        for recommendation in recommendations_data
                        if recommendation.get('algorithm_version')
                    ),
                    None,
                )
            ),
            'generated_at': generated_at.strftime('%d %B %Y %H:%M %Z'),
            'logo_path': logo_path,
        }

        pdf_bytes = build_student_report(data)
        today = date.today().isoformat()
        safe_first = re.sub(r'[^\w-]', '', student.first_name)
        safe_last = re.sub(r'[^\w-]', '', student.last_name)
        filename = f'smarta-shauri-report-{safe_first}-{safe_last}-{today}.pdf'

        log_action(
            actor=request.user,
            action='report_downloaded',
            target_type='report',
            target_id=student.id,
            details={
                'student_id': student.id,
                'requester_role': request.user.role,
                'filename': filename,
            },
            request=request,
        )

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _membership_context(self, profile):
        if profile.report_has_membership_history:
            return {
                'uses_membership_history': True,
                'school_id': profile.report_active_school_id,
                'school_name': profile.report_active_school_name,
                'status': profile.report_active_membership_status,
            }
        return {
            'uses_membership_history': False,
            'school_id': profile.school_id,
            'school_name': profile.school.name if profile.school else None,
            'status': profile.school_membership_status,
        }

    def _has_access(self, user, student, profile, membership_context):
        if user.role == 'system_admin':
            return True
        if user.role == 'student':
            return user.id == student.id
        if user.role == 'counselor':
            return CounselorAssignment.objects.filter(
                counselor=user, student_profile=profile, is_active=True,
            ).exists()
        if user.role == 'school_admin':
            if membership_context['uses_membership_history']:
                return (
                    membership_context['school_id'] == user.school_id
                    and membership_context['status']
                    == StudentSchoolMembership.STATUS_ACTIVE
                )
            return (
                profile.mode == 'school_linked'
                and profile.school_membership_status == 'active'
                and profile.school_id is not None
                and profile.school_id == user.school_id
            )
        if user.role == 'parent':
            return ParentStudentLink.objects.filter(
                parent=user,
                student=student,
                status=ParentStudentLink.STATUS_ACTIVE,
            ).exists()
        return False

    def _get_subjects_data(self, profile, enrollments=None):
        if enrollments is None:
            enrollments = academic_support_enrolments(profile)
        subjects = []
        for enrollment in enrollments:
            grades = [
                {
                    'term': g.term,
                    'year': g.year,
                    'level': g.level,
                    'label': GRADE_LABELS.get(g.level, g.level),
                    'framework': {
                        'code': g.framework.code,
                        'version': g.framework.version,
                    },
                    'source': g.source,
                    'verified_school': (
                        g.verified_school.name
                        if g.verified_school_id is not None
                        else None
                    ),
                    'verified_at': (
                        timezone.localtime(g.verified_at).strftime('%d %B %Y')
                        if g.verified_at is not None
                        else None
                    ),
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
            'instrument_version': assessment.instrument_version,
            'submitted_at': timezone.localtime(
                assessment.submitted_at
            ).strftime('%d %B %Y'),
        }

        recommendations = []
        for rec in assessment.recommendations.select_related('pathway').all()[:3]:
            recommendations.append({
                'rank': rec.rank,
                'pathway_name': rec.pathway.name,
                'algorithm_version': rec.algorithm_version,
                'explanation': rec.explanation,
            })

        return riasec_data, recommendations

    def _get_plan_context(self, profile):
        plan = (
            LearnerPlan.objects
            .filter(student_profile=profile)
            .select_related(
                'provisional_choice__combination__framework_version',
                'provisional_choice__combination__track__pathway',
                'provisional_choice__combination__subject_one',
                'provisional_choice__combination__subject_two',
                'provisional_choice__combination__subject_three',
            )
            .prefetch_related('milestones')
            .first()
        )
        if plan:
            return plan, plan.provisional_choice

        choice = (
            LearnerCombinationChoice.objects
            .filter(
                student_profile=profile,
                status=LearnerCombinationChoice.STATUS_PROVISIONAL,
            )
            .select_related(
                'combination__framework_version',
                'combination__track__pathway',
                'combination__subject_one',
                'combination__subject_two',
                'combination__subject_three',
            )
            .first()
        )
        return None, choice

    def _serialize_choice(self, choice):
        if choice is None:
            return None
        combination = choice.combination
        return {
            'code': combination.code,
            'title': combination.title,
            'pathway': combination.track.pathway.name,
            'track': combination.track.name,
            'subjects': [subject.name for subject in combination.subjects],
            'learner_reason': choice.learner_reason,
        }

    def _serialize_plan(self, plan):
        if plan is None:
            return None
        return {
            'review_status': plan.review_status,
            'learner_reason': plan.learner_reason,
            'milestones': [
                {
                    'title': milestone.title,
                    'due_date': (
                        milestone.due_date.strftime('%d %B %Y')
                        if milestone.due_date else None
                    ),
                    'is_complete': milestone.is_complete,
                }
                for milestone in plan.milestones.all()
            ],
        }


class SchoolOverviewReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', 404)
        stats = get_school_stats(school)
        total = stats['total_students']
        pdf_bytes = build_cohort_overview_report({
            'title': 'School Overview',
            'subtitle': school.name,
            'generated_at': timezone.localtime().strftime('%d %B %Y %H:%M %Z'),
            'logo_path': _logo_path(),
            'stats': [
                {'label': 'Active learners', 'value': total},
                {'label': 'Assessed', 'value': f"{_percent(stats['assessed'], total)}%", 'sublabel': f"{stats['assessed']} of {total}"},
                {'label': 'Evidence complete', 'value': f"{_percent(stats['evidence_complete'], total)}%", 'sublabel': f"{stats['evidence_complete']} of {total}"},
                {'label': 'Choices saved', 'value': stats['choices_saved']},
                {'label': 'Plans reviewed', 'value': stats['reviews_completed']},
                {'label': 'Unassigned', 'value': stats['unassigned']},
                {'label': 'Pending memberships', 'value': stats['pending_memberships']},
            ],
            'counselor_workload': stats['counselor_workload'],
        })
        filename = f"smarta-shauri-school-overview-{_safe_scope(school.name)}-{date.today().isoformat()}.pdf"
        log_action(
            actor=request.user, action='report_downloaded', target_type='report',
            target_id=school.id,
            details={'report_type': 'school_overview', 'requester_role': request.user.role},
            request=request,
        )
        return _pdf_response(pdf_bytes, filename)


class SchoolRosterReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSchoolAdmin]

    def get(self, request):
        school = request.user.school
        if not school:
            return _error('No school assigned to your account.', 404)
        grade, error = _grade_filter(request)
        if error:
            return error
        rows = get_school_roster(school, grade)
        grade_label = f'Grade {grade}' if grade else 'All grades'
        pdf_bytes = build_cohort_roster_report({
            'title': 'School Learner Roster',
            'subtitle': f'{school.name} · {grade_label}',
            'generated_at': timezone.localtime().strftime('%d %B %Y %H:%M %Z'),
            'logo_path': _logo_path(),
            'rows': rows,
            'include_counselor': True,
        })
        filename = f"smarta-shauri-school-roster-{_safe_scope(school.name)}-{date.today().isoformat()}.pdf"
        log_action(
            actor=request.user, action='report_downloaded', target_type='report',
            target_id=school.id,
            details={
                'report_type': 'school_roster', 'grade_filter': grade,
                'requester_role': request.user.role,
            }, request=request,
        )
        return _pdf_response(pdf_bytes, filename)


class CounselorOverviewReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        stats = get_caseload_stats(request.user)
        total = stats['total_students']
        name = f'{request.user.first_name} {request.user.last_name}'.strip()
        pdf_bytes = build_cohort_overview_report({
            'title': 'Caseload Overview',
            'subtitle': name or request.user.email,
            'generated_at': timezone.localtime().strftime('%d %B %Y %H:%M %Z'),
            'logo_path': _logo_path(),
            'stats': [
                {'label': 'Active learners', 'value': total},
                {'label': 'Assessed', 'value': f"{_percent(stats['assessments_done'], total)}%", 'sublabel': f"{stats['assessments_done']} of {total}"},
                {'label': 'Evidence complete', 'value': f"{_percent(stats['evidence_complete'], total)}%", 'sublabel': f"{stats['evidence_complete']} of {total}"},
                {'label': 'Choices saved', 'value': stats['choices_saved']},
                {'label': 'Plans reviewed', 'value': stats['journeys_reviewed']},
                {'label': 'Need attention', 'value': stats['students_needing_attention']},
                {'label': 'Follow-ups due', 'value': stats['follow_ups_due']},
            ],
        })
        filename = f"smarta-shauri-caseload-overview-{_safe_scope(name)}-{date.today().isoformat()}.pdf"
        log_action(
            actor=request.user, action='report_downloaded', target_type='report',
            target_id=request.user.id,
            details={'report_type': 'counselor_overview', 'requester_role': request.user.role},
            request=request,
        )
        return _pdf_response(pdf_bytes, filename)


class CounselorRosterReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        grade, error = _grade_filter(request)
        if error:
            return error
        rows = get_caseload_roster(request.user, grade)
        grade_label = f'Grade {grade}' if grade else 'All grades'
        pdf_bytes = build_cohort_roster_report({
            'title': 'Caseload Roster',
            'subtitle': grade_label,
            'generated_at': timezone.localtime().strftime('%d %B %Y %H:%M %Z'),
            'logo_path': _logo_path(),
            'rows': rows,
            'include_counselor': False,
        })
        filename = f"smarta-shauri-caseload-roster-{date.today().isoformat()}.pdf"
        log_action(
            actor=request.user, action='report_downloaded', target_type='report',
            target_id=request.user.id,
            details={
                'report_type': 'counselor_roster', 'grade_filter': grade,
                'requester_role': request.user.role,
            }, request=request,
        )
        return _pdf_response(pdf_bytes, filename)


class PlatformOverviewReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSystemAdmin]

    def get(self, request):
        stats = get_platform_stats()
        registered = stats['registered_learners']
        coverage = stats['assignment_coverage']
        roles = stats['users_by_role']
        counties = sorted(set(stats['schools_by_county']) | set(stats['learners_by_county']))
        pdf_bytes = build_platform_overview_report({
            'generated_at': timezone.localtime().strftime('%d %B %Y %H:%M %Z'),
            'logo_path': _logo_path(),
            'stats': [
                {'label': 'Learners', 'value': registered},
                {'label': 'Counsellors', 'value': roles.get('counselor', 0)},
                {'label': 'Schools', 'value': stats['total_schools']},
                {'label': 'Verified learners', 'value': f"{_percent(stats['verified_learners'], registered)}%"},
                {'label': 'Assignment coverage', 'value': f"{coverage['percent']}%", 'sublabel': f"{coverage['assigned']} of {coverage['eligible']}"},
                {'label': 'Plans completed', 'value': stats['plans_completed']},
                {'label': 'Recent signups', 'value': stats['recent_signups'], 'sublabel': 'Last 7 days'},
            ],
            'counties': [{
                'county': county.replace('_', ' ').title(),
                'schools': stats['schools_by_county'].get(county, 0),
                'learners': stats['learners_by_county'].get(county, 0),
            } for county in counties],
        })
        filename = f'smarta-shauri-platform-overview-{date.today().isoformat()}.pdf'
        log_action(
            actor=request.user, action='report_downloaded', target_type='report',
            target_id=0,
            details={'report_type': 'system_overview', 'requester_role': request.user.role},
            request=request,
        )
        return _pdf_response(pdf_bytes, filename)


class SchoolsDirectoryReportView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsSystemAdmin]

    def get(self, request):
        pdf_bytes = build_schools_directory_report({
            'generated_at': timezone.localtime().strftime('%d %B %Y %H:%M %Z'),
            'logo_path': _logo_path(),
            'schools': get_schools_directory(),
        })
        filename = f'smarta-shauri-schools-directory-{date.today().isoformat()}.pdf'
        log_action(
            actor=request.user, action='report_downloaded', target_type='report',
            target_id=0,
            details={'report_type': 'system_schools', 'requester_role': request.user.role},
            request=request,
        )
        return _pdf_response(pdf_bytes, filename)
