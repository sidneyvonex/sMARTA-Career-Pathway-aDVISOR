"""Read-only academic support context shared with authorized supporting roles."""

from django.db.models import Prefetch

from tertiary.models import LearnerEducationGoal
from tertiary.serializers import LearnerEducationGoalSerializer

from .models import AcademicGoal, CBCGrade, StudentSubject
from .progress import derive_progress_for_enrolments
from .serializers import AcademicGoalSerializer, ProgressAssessmentSerializer


def academic_support_enrolment_queryset():
    """Return the complete enrollment graph used by supporting-role reads."""
    return (
        StudentSubject.objects.select_related('subject')
        .prefetch_related(
            Prefetch(
                'grades',
                queryset=(
                    CBCGrade.objects.select_related(
                        'framework',
                        'verified_school',
                    )
                    .prefetch_related('framework__level_definitions')
                    .order_by('academic_grade', 'year', 'term', 'created_at', 'pk')
                ),
            )
        )
    )


def academic_support_enrolments(profile):
    prefetched = getattr(profile, 'support_enrolments', None)
    if prefetched is not None:
        return prefetched
    return list(
        academic_support_enrolment_queryset().filter(student_profile=profile)
    )


def academic_support_context(profile, *, enrolments=None):
    """Return the learner-owned progress and goal contracts without mutation APIs."""
    if enrolments is None:
        enrolments = academic_support_enrolments(profile)
    progress = derive_progress_for_enrolments(enrolments)
    academic_goals = list(
        AcademicGoal.objects.filter(learner=profile).select_related(
            'current_evidence__student_subject',
            'current_level_definition__framework',
            'target_level_definition__framework',
            'created_by',
        )
    )
    goal_context = {
        'academic_goal_readiness': AcademicGoal.batch_readiness(academic_goals),
    }
    education_goals = (
        LearnerEducationGoal.objects.filter(learner=profile).select_related(
            'institution', 'programme', 'programme__institution'
        )
    )
    return {
        'academic_progress': ProgressAssessmentSerializer(progress).data,
        'academic_goals': AcademicGoalSerializer(
            academic_goals,
            many=True,
            context=goal_context,
        ).data,
        'education_goals': LearnerEducationGoalSerializer(
            education_goals,
            many=True,
        ).data,
    }
