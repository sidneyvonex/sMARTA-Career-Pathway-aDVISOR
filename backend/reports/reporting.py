"""Shared queryset and row shaping helpers for cohort reports."""

from django.db.models import Count, Exists, OuterRef, Prefetch, Q

from counselors.models import CounselorAssignment
from guidance.models import LearnerPlan
from riasec.models import RIASECAssessment


def cohort_roster_queryset(queryset, grade=None):
    assessment = RIASECAssessment.objects.filter(student_profile=OuterRef('pk'))
    assignments = CounselorAssignment.objects.filter(
        is_active=True,
    ).select_related('counselor')
    if grade is not None:
        queryset = queryset.filter(grade=grade)
    return (
        queryset.select_related('user', 'school')
        .annotate(
            has_assessment=Exists(assessment),
            enrolled_subject_count=Count(
                'enrolled_subjects',
                filter=Q(enrolled_subjects__is_active=True),
                distinct=True,
            ),
            subjects_with_evidence=Count(
                'enrolled_subjects',
                filter=Q(
                    enrolled_subjects__is_active=True,
                    enrolled_subjects__grades__isnull=False,
                ),
                distinct=True,
            ),
        )
        .prefetch_related(
            Prefetch(
                'counselor_assignments',
                queryset=assignments,
                to_attr='report_assignments',
            ),
            'learner_plan',
        )
        .order_by('grade', 'user__first_name', 'user__last_name', 'pk')
    )


def cohort_roster_rows(queryset, include_counselor=False):
    rows = []
    plan_labels = dict(LearnerPlan.STATUS_CHOICES)
    for profile in queryset:
        try:
            plan = profile.learner_plan
        except LearnerPlan.DoesNotExist:
            plan = None
        row = {
            'name': f'{profile.user.first_name} {profile.user.last_name}'.strip(),
            'grade': profile.grade,
            'riasec_status': 'Complete' if profile.has_assessment else 'Pending',
            'subjects_enrolled': profile.enrolled_subject_count,
            'subjects_with_evidence': profile.subjects_with_evidence,
            'plan_status': plan_labels.get(plan.review_status, 'Not started') if plan else 'Not started',
        }
        if include_counselor:
            assignment = next(iter(profile.report_assignments), None)
            row['counselor'] = (
                f'{assignment.counselor.first_name} {assignment.counselor.last_name}'.strip()
                if assignment else 'Unassigned'
            )
        rows.append(row)
    return rows
