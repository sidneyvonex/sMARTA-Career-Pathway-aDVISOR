from dataclasses import dataclass
from datetime import date

from django.db.models import Prefetch
from django.utils import timezone

from guidance.models import LearnerCombinationChoice, SchoolOffering
from riasec.models import RIASECAssessment, Recommendation
from students.models import CBCGrade, StudentSubject


ATTENTION_REASON_CONTENT = {
    'assessment_missing': {
        'label': 'Interest assessment missing',
        'guidance': 'Invite the learner to complete the interest assessment.',
    },
    'academic_evidence_missing': {
        'label': 'Academic evidence incomplete',
        'guidance': 'Review the enrolled subjects and add missing grade evidence.',
    },
    'no_saved_combination': {
        'label': 'No saved combination',
        'guidance': 'Help the learner explore and save suitable pilot combinations.',
    },
    'no_plan': {
        'label': 'No learner plan',
        'guidance': 'Support the learner to turn a provisional choice into a plan.',
    },
    'learner_requested_review': {
        'label': 'Review requested',
        'guidance': 'Review the learner plan and record the agreed next step.',
    },
    'follow_up_overdue': {
        'label': 'Follow-up overdue',
        'guidance': 'Complete or reschedule the open follow-up.',
    },
    'combination_unavailable_at_school': {
        'label': 'Combination not offered by school',
        'guidance': 'Discuss another offering or an appropriate school option.',
    },
}


@dataclass(frozen=True)
class AttentionSnapshot:
    assessment_complete: bool
    academic_evidence_ready: bool
    saved_combination_count: int
    has_plan: bool
    learner_requested_review: bool
    follow_up_overdue: bool
    selected_combination_available: bool


def derive_attention_reasons(snapshot):
    checks = (
        ('assessment_missing', not snapshot.assessment_complete),
        ('academic_evidence_missing', not snapshot.academic_evidence_ready),
        ('no_saved_combination', snapshot.saved_combination_count == 0),
        ('no_plan', not snapshot.has_plan),
        ('learner_requested_review', snapshot.learner_requested_review),
        ('follow_up_overdue', snapshot.follow_up_overdue),
        (
            'combination_unavailable_at_school',
            not snapshot.selected_combination_available,
        ),
    )
    return [
        {'code': code, **ATTENTION_REASON_CONTENT[code]}
        for code, applies in checks
        if applies
    ]


def attention_profiles(queryset):
    """Load every evidence source with a caseload-bounded query count."""
    return queryset.select_related(
        'school',
        'learner_plan__provisional_choice',
    ).prefetch_related(
        Prefetch(
            'riasec_assessments',
            queryset=RIASECAssessment.objects.only(
                'id',
                'student_profile_id',
                'submitted_at',
            ).prefetch_related(
                Prefetch(
                    'recommendations',
                    queryset=Recommendation.objects.select_related(
                        'pathway'
                    ).order_by('rank'),
                )
            ).order_by('-submitted_at', '-pk'),
            to_attr='attention_assessments',
        ),
        Prefetch(
            'enrolled_subjects',
            queryset=StudentSubject.objects.prefetch_related(
                Prefetch(
                    'grades',
                    queryset=CBCGrade.objects.only('id', 'student_subject_id'),
                    to_attr='attention_grades',
                )
            ).only('id', 'student_profile_id'),
            to_attr='attention_subjects',
        ),
        Prefetch(
            'combination_choices',
            queryset=LearnerCombinationChoice.objects.only(
                'id',
                'student_profile_id',
                'combination_id',
                'status',
            ),
            to_attr='attention_choices',
        ),
        Prefetch(
            'school__guidance_offerings',
            queryset=SchoolOffering.objects.filter(is_active=True).only(
                'id',
                'school_id',
                'combination_id',
            ),
            to_attr='attention_offerings',
        ),
    )


def _has_overdue_follow_up(follow_ups, today):
    return any(
        getattr(item, 'status', None) == 'open'
        and getattr(item, 'follow_up_date', None) is not None
        and item.follow_up_date < today
        for item in follow_ups
    )


def _selected_combination_available(profile, plan, choices):
    if not getattr(profile, 'school_id', None):
        return True

    provisional_choice = (
        getattr(plan, 'provisional_choice', None) if plan else None
    )
    if provisional_choice is None:
        provisional_choice = next(
            (
                choice for choice in choices
                if choice.status == LearnerCombinationChoice.STATUS_PROVISIONAL
            ),
            None,
        )
    if provisional_choice is None:
        return True

    offerings = getattr(profile.school, 'attention_offerings', [])
    offered_combination_ids = {
        offering.combination_id for offering in offerings
    }
    return provisional_choice.combination_id in offered_combination_ids


def attention_reasons_for(profile, *, follow_ups=(), today=None):
    assessments = getattr(profile, 'attention_assessments', [])
    subjects = getattr(profile, 'attention_subjects', [])
    choices = getattr(profile, 'attention_choices', [])
    plan = getattr(profile, 'learner_plan', None)

    academic_evidence_ready = (
        len(subjects) >= 3
        and all(
            len(getattr(subject, 'attention_grades', [])) > 0
            for subject in subjects
        )
    )
    snapshot = AttentionSnapshot(
        assessment_complete=bool(assessments),
        academic_evidence_ready=academic_evidence_ready,
        saved_combination_count=len(choices),
        has_plan=plan is not None,
        learner_requested_review=(
            plan is not None and plan.review_status == 'ready_for_review'
        ),
        follow_up_overdue=_has_overdue_follow_up(
            follow_ups,
            today or timezone.localdate(),
        ),
        selected_combination_available=_selected_combination_available(
            profile,
            plan,
            choices,
        ),
    )
    return derive_attention_reasons(snapshot)
