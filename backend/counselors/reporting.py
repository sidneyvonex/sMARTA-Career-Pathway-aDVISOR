"""Reusable counsellor dashboard and report statistics."""

from django.utils import timezone

from guidance.models import LearnerCombinationChoice, LearnerPlan
from reports.reporting import cohort_roster_queryset, cohort_roster_rows
from .attention import attention_profiles, attention_reasons_for
from .models import CounselorIntervention, CounselorNote


def active_caseload_profiles(counselor):
    from accounts.models import StudentProfile
    return StudentProfile.objects.filter(
        counselor_assignments__counselor=counselor,
        counselor_assignments__is_active=True,
    ).distinct()


def get_caseload_stats(counselor):
    base = active_caseload_profiles(counselor)
    profiles = list(attention_profiles(base.select_related('user', 'school')))
    profile_ids = [profile.pk for profile in profiles]
    total = len(profiles)
    assessed = sum(bool(profile.attention_assessments) for profile in profiles)
    needing_attention = sum(bool(attention_reasons_for(profile)) for profile in profiles)
    reviewed = sum(
        getattr(profile, 'learner_plan', None) is not None
        and profile.learner_plan.review_status == LearnerPlan.STATUS_REVIEWED
        for profile in profiles
    )
    evidence_complete = 0
    for profile in profiles:
        subjects = profile.attention_subjects
        if len(subjects) >= 3 and all(subject.attention_grades for subject in subjects):
            evidence_complete += 1
    notes = CounselorNote.objects.filter(
        counselor=counselor,
        deleted_at__isnull=True,
        student__student_profile__id__in=profile_ids,
    ).count()
    follow_ups_due = CounselorIntervention.objects.filter(
        counselor=counselor,
        student__student_profile__id__in=profile_ids,
        status=CounselorIntervention.STATUS_OPEN,
        follow_up_date__lte=timezone.localdate(),
    ).count()
    return {
        'total_students': total,
        'assessments_done': assessed,
        'students_needing_attention': needing_attention,
        'follow_ups_due': follow_ups_due,
        'journeys_reviewed': reviewed,
        'notes_written': notes,
        'evidence_complete': evidence_complete,
        'choices_saved': LearnerCombinationChoice.objects.filter(
            student_profile_id__in=profile_ids,
        ).values('student_profile_id').distinct().count(),
        'plans_created': LearnerPlan.objects.filter(
            student_profile_id__in=profile_ids,
        ).count(),
    }


def get_caseload_roster(counselor, grade=None):
    queryset = cohort_roster_queryset(active_caseload_profiles(counselor), grade)
    return cohort_roster_rows(queryset, include_counselor=False)
